#include <dispatch/dispatch.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <xpc/xpc.h>

#define DEFAULT_SERVICE "com.example.ctypes-xpc.raw-c"

static void print_xpc_event(const char *prefix, xpc_object_t event)
{
    char *description = xpc_copy_description(event);
    fprintf(
        stderr,
        "%s: %s\n",
        prefix,
        description != NULL ? description : "<no description>");
    free(description);
}

static void send_reply(xpc_connection_t peer, xpc_object_t request)
{
    const char *op = xpc_dictionary_get_string(request, "op");
    xpc_object_t reply = xpc_dictionary_create_reply(request);
    if (reply == NULL) {
        fprintf(stderr, "request had no reply context\n");
        return;
    }

    if (op != NULL && strcmp(op, "add") == 0) {
        int64_t a = xpc_dictionary_get_int64(request, "a");
        int64_t b = xpc_dictionary_get_int64(request, "b");
        int64_t sum;
        if (__builtin_add_overflow(a, b, &sum)) {
            xpc_dictionary_set_bool(reply, "ok", false);
            xpc_dictionary_set_string(reply, "error", "signed 64-bit overflow");
        }
        else {
            xpc_dictionary_set_bool(reply, "ok", true);
            xpc_dictionary_set_int64(reply, "sum", sum);
            xpc_dictionary_set_string(reply, "server", "c");
        }
    }
    else if (op != NULL && strcmp(op, "notify") == 0) {
        const char *text = xpc_dictionary_get_string(request, "text");
        xpc_object_t event = xpc_dictionary_create(NULL, NULL, 0);
        xpc_dictionary_set_string(event, "event", "notice");
        xpc_dictionary_set_string(
            event,
            "text",
            text != NULL ? text : "hello from C");
        xpc_connection_send_message(peer, event);
        xpc_release(event);

        xpc_dictionary_set_bool(reply, "ok", true);
        xpc_dictionary_set_string(reply, "server", "c");
    }
    else {
        xpc_dictionary_set_bool(reply, "ok", false);
        xpc_dictionary_set_string(reply, "error", "unknown operation");
    }

    xpc_connection_send_message(peer, reply);
    xpc_release(reply);
}

static int run_service(const char *service_name)
{
    xpc_connection_t listener = xpc_connection_create_mach_service(
        service_name,
        NULL,
        XPC_CONNECTION_MACH_SERVICE_LISTENER);
    if (listener == NULL) {
        fprintf(stderr, "could not create listener\n");
        return EXIT_FAILURE;
    }

    xpc_connection_set_event_handler(listener, ^(xpc_object_t event) {
        if (xpc_get_type(event) != XPC_TYPE_CONNECTION) {
            print_xpc_event("listener event", event);
            return;
        }

        xpc_connection_t peer = (xpc_connection_t)event;
        if (xpc_connection_get_euid(peer) != geteuid()) {
            fprintf(stderr, "rejecting peer with a different effective UID\n");
            xpc_connection_cancel(peer);
            return;
        }

        xpc_connection_set_event_handler(peer, ^(xpc_object_t peer_event) {
            xpc_type_t type = xpc_get_type(peer_event);
            if (type == XPC_TYPE_DICTIONARY) {
                send_reply(peer, peer_event);
            }
            else if (type == XPC_TYPE_ERROR) {
                print_xpc_event("peer event", peer_event);
            }
        });
        xpc_connection_resume(peer);
    });

    xpc_connection_resume(listener);
    fprintf(stdout, "C service listening on %s\n", service_name);
    fflush(stdout);
    dispatch_main();
}

static int run_client(const char *service_name)
{
    xpc_connection_t connection = xpc_connection_create_mach_service(
        service_name,
        NULL,
        0);
    if (connection == NULL) {
        fprintf(stderr, "could not create client connection\n");
        return EXIT_FAILURE;
    }

    xpc_connection_set_event_handler(connection, ^(xpc_object_t event) {
        xpc_type_t type = xpc_get_type(event);
        if (type == XPC_TYPE_DICTIONARY) {
            const char *kind = xpc_dictionary_get_string(event, "event");
            const char *text = xpc_dictionary_get_string(event, "text");
            fprintf(
                stdout,
                "unsolicited %s: %s\n",
                kind != NULL ? kind : "message",
                text != NULL ? text : "<no text>");
        }
        else if (type == XPC_TYPE_ERROR) {
            print_xpc_event("connection event", event);
        }
    });
    xpc_connection_resume(connection);

    xpc_object_t request = xpc_dictionary_create(NULL, NULL, 0);
    xpc_dictionary_set_string(request, "op", "add");
    xpc_dictionary_set_int64(request, "a", 20);
    xpc_dictionary_set_int64(request, "b", 22);

    xpc_object_t reply = xpc_connection_send_message_with_reply_sync(
        connection,
        request);
    xpc_release(request);

    if (reply == NULL || xpc_get_type(reply) == XPC_TYPE_ERROR) {
        if (reply != NULL) {
            print_xpc_event("request failed", reply);
            xpc_release(reply);
        }
        else {
            fprintf(stderr, "request returned NULL\n");
        }
        xpc_connection_cancel(connection);
        xpc_release(connection);
        return EXIT_FAILURE;
    }

    const char *server = xpc_dictionary_get_string(reply, "server");
    fprintf(
        stdout,
        "20 + 22 = %" PRId64 " (server=%s)\n",
        xpc_dictionary_get_int64(reply, "sum"),
        server != NULL ? server : "<unknown>");
    xpc_release(reply);

    request = xpc_dictionary_create(NULL, NULL, 0);
    xpc_dictionary_set_string(request, "op", "notify");
    xpc_dictionary_set_string(
        request,
        "text",
        "hello across the language boundary");
    reply = xpc_connection_send_message_with_reply_sync(connection, request);
    xpc_release(request);
    if (reply == NULL || xpc_get_type(reply) == XPC_TYPE_ERROR) {
        if (reply != NULL) {
            print_xpc_event("notification request failed", reply);
            xpc_release(reply);
        }
        xpc_connection_cancel(connection);
        xpc_release(connection);
        return EXIT_FAILURE;
    }
    xpc_release(reply);

    /* Give the unsolicited event handler a moment to run before cancellation. */
    dispatch_after(
        dispatch_time(DISPATCH_TIME_NOW, 250 * NSEC_PER_MSEC),
        dispatch_get_main_queue(),
        ^{
            xpc_connection_cancel(connection);
            xpc_release(connection);
            exit(EXIT_SUCCESS);
        });
    dispatch_main();
}

int main(int argc, char **argv)
{
    if (
        argc < 2 ||
        (strcmp(argv[1], "client") != 0 && strcmp(argv[1], "service") != 0)
    ) {
        fprintf(stderr, "usage: %s {client|service} [service-name]\n", argv[0]);
        return EXIT_FAILURE;
    }
    const char *service_name = argc >= 3 ? argv[2] : DEFAULT_SERVICE;
    return strcmp(argv[1], "service") == 0
        ? run_service(service_name)
        : run_client(service_name);
}
