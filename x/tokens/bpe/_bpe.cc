// @om-cext
#define PY_SSIZE_T_CLEAN
#include "Python.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <exception>
#include <functional>
#include <memory>
#include <new>
#include <string>
#include <string_view>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>

// A byte pair encoding trainer and encoder in the style of GPT-4's tokenizer: a regex splits text into chunks, a chunk
// starts out as its UTF-8 bytes, and training repeatedly replaces the most frequent adjacent pair of tokens with a new
// one. It is a port of https://github.com/karpathy/rustbpe - it keeps that library's interface, and from the same text
// learns the same merges - with PCRE2 in place of fancy-regex, reached through the capsule omcore's _pcre2 exports
// rather than linked.
//
// A Tokenizer is a reference to an immutable model: its pattern, and the merges learned for it. Training builds a new
// model off to one side and swaps it in only once complete, so every other method works from whichever model was
// current when it was called, never from one half made, and a training which fails changes nothing. Any number of
// threads may therefore use one Tokenizer at once, training included - of two trainings at once the last to finish
// wins.
//
// All of the heavy work - splitting, counting, merging, and encoding anything of size - is done with the thread state
// detached, and touches no Python object while it is.

//

#define _MODULE_NAME "_bpe"
#define _PACKAGE_NAME "omllm.tokens.bpe"
#define _MODULE_FULL_NAME _PACKAGE_NAME "." _MODULE_NAME

//

// PCRE2 is used only through the table of functions _pcre2 exports: none of it is linked here, and its header, which
// is vendored inside omcore's extension, is not one this package can include. So this restates the little of pcre2.h
// that is needed, as it reads for 8-bit code units, and then the leading part of the table as _pcre2.c declares it -
// entries are only ever appended to that under an abi version, so a consumer may declare as much of it as it uses.

extern "C" {

struct pcre2_real_general_context_8;
struct pcre2_real_compile_context_8;
struct pcre2_real_match_context_8;
struct pcre2_real_code_8;
struct pcre2_real_match_data_8;

}

typedef struct pcre2_real_general_context_8 pcre2_general_context;
typedef struct pcre2_real_compile_context_8 pcre2_compile_context;
typedef struct pcre2_real_match_context_8 pcre2_match_context;
typedef struct pcre2_real_code_8 pcre2_code;
typedef struct pcre2_real_match_data_8 pcre2_match_data;

typedef uint8_t PCRE2_UCHAR;
typedef const PCRE2_UCHAR *PCRE2_SPTR;
typedef size_t PCRE2_SIZE;

#define PCRE2_NO_UTF_CHECK 0x40000000u
#define PCRE2_UCP 0x00020000u
#define PCRE2_UTF 0x00080000u
#define PCRE2_NEVER_BACKSLASH_C 0x00100000u
#define PCRE2_MATCH_INVALID_UTF 0x04000000u

#define PCRE2_ERROR_NOMATCH (-1)
#define PCRE2_ERROR_BADDATA (-29)
#define PCRE2_ERROR_MATCHLIMIT (-47)
#define PCRE2_ERROR_NOMEMORY (-48)

#define PCRE2_INFO_ALLOPTIONS 0

#define PCRE2_CAPI_MODULE_NAME "omcore.text.pcre2._pcre2"
#define PCRE2_CAPI_CAPSULE_NAME PCRE2_CAPI_MODULE_NAME ".capi"
#define PCRE2_CAPI_ABI_VERSION 1

typedef struct Pcre2Capi {
    uint32_t abi_version;
    uint32_t struct_size;

    const pcre2_code * (*code_from_object)(PyObject *obj);

    pcre2_code * (*compile)(PCRE2_SPTR, PCRE2_SIZE, uint32_t, int *, PCRE2_SIZE *, pcre2_compile_context *);
    void (*code_free)(pcre2_code *);
    int (*pattern_info)(const pcre2_code *, uint32_t, void *);

    pcre2_match_data * (*match_data_create)(uint32_t, pcre2_general_context *);
    pcre2_match_data * (*match_data_create_from_pattern)(const pcre2_code *, pcre2_general_context *);
    void (*match_data_free)(pcre2_match_data *);

    int (*match)(
        const pcre2_code *,
        PCRE2_SPTR,
        PCRE2_SIZE,
        PCRE2_SIZE,
        uint32_t,
        pcre2_match_data *,
        pcre2_match_context *
    );
    int (*next_match)(pcre2_match_data *, PCRE2_SIZE *, uint32_t *);

    PCRE2_SIZE * (*get_ovector_pointer)(pcre2_match_data *);
    uint32_t (*get_ovector_count)(pcre2_match_data *);
    PCRE2_SIZE (*get_startchar)(pcre2_match_data *);

    int (*get_error_message)(int, PCRE2_UCHAR *, PCRE2_SIZE);

    pcre2_match_context * (*match_context_from_object)(PyObject *obj);

    pcre2_match_context * (*match_context_create)(pcre2_general_context *);
    void (*match_context_free)(pcre2_match_context *);
    int (*set_match_limit)(pcre2_match_context *, uint32_t);
    int (*set_depth_limit)(pcre2_match_context *, uint32_t);
    int (*set_heap_limit)(pcre2_match_context *, uint32_t);
    int (*set_offset_limit)(pcre2_match_context *, PCRE2_SIZE);
} Pcre2Capi;

//

// What rustbpe splits with unless told otherwise.
#define GPT4_PATTERN \
    "'(?i:[sdmt]|ll|ve|re)|" \
    "[^\\r\\n\\p{L}\\p{N}]?+\\p{L}+|" \
    "\\p{N}{1,3}|" \
    " ?[^\\s\\p{L}\\p{N}]++[\\r\\n]*|" \
    "\\s*[\\r\\n]|" \
    "\\s+(?!\\S)|" \
    "\\s+"

// UTF and UCP are what make PCRE2 read a pattern the way fancy-regex does: as, and against, Unicode. \C matches a
// single byte, and so can end a match in the middle of a character - where the next search of the text would then
// start, which is not something PCRE2 may be asked to do without checking the text again. Rust's regexes have no \C
// either.
static const uint32_t kCompileOptions = PCRE2_UTF | PCRE2_UCP | PCRE2_NEVER_BACKSLASH_C;

// Work on less text than this is done without detaching from the interpreter, as detaching for so little costs more
// than it frees up - with a GIL, reattaching can mean waiting out whichever thread took it in the meantime. That
// leaves the interpreter held for as long as the regex takes, which for one that backtracks badly is no small time
// even over a short text, so such work is run under a match limit low enough to cut that short, and is redone
// detached, without it, if the limit is hit.
static const size_t kDetachSize = 1024;
static const uint32_t kProbeMatchLimit = 256;

// How much text it takes to be worth another thread.
static const size_t kWorkerSize = 32 * 1024;

static const long long kMaxThreads = 256;

// Chunks longer than this are encoded by encode_long_chunk, whose bookkeeping only pays for itself on them.
static const size_t kLongChunkSize = 128;

// How long merging runs between checks for signals, by which it can be interrupted.
static const std::chrono::milliseconds kPollInterval{50};

// Errors of this module's own, alongside PCRE2's, from which they are kept well clear.
static const int kErrorInterrupted = -1000;
static const int kErrorTooManyChunks = -1001;

//

// A pair of adjacent tokens, packed such that pairs order as (left, right) tuples do.
typedef uint64_t Pair;

static inline Pair make_pair(uint32_t left, uint32_t right)
{
    return ((Pair)left << 32) | right;
}

static inline uint32_t pair_left(Pair pair)
{
    return (uint32_t)(pair >> 32);
}

static inline uint32_t pair_right(Pair pair)
{
    return (uint32_t)pair;
}

// The most tokens a vocabulary may have. It keeps every token below 2^32 - 1, which leaves that free to mean no
// token, and the pair of two of them free to mean no pair.
static const long long kMaxVocabSize = 0xFFFFFFFFLL;
static const uint32_t kNoToken = 0xFFFFFFFFu;
static const Pair kNoPair = ~(Pair)0;

// An open-addressed map keyed by pairs, for the lookups which dominate both training and encoding. Entries are never
// removed.
template <typename V>
class PairMap {
public:
    const V * find(Pair key) const
    {
        if (slots_.empty()) {
            return nullptr;
        }
        for (size_t i = hash(key) & mask_; ; i = (i + 1) & mask_) {
            const Slot &slot = slots_[i];
            if (slot.key == key) {
                return &slot.value;
            }
            if (slot.key == kNoPair) {
                return nullptr;
            }
        }
    }

    // The value for key, which is added with a zero value if absent. Invalidated by the next call.
    V & operator[](Pair key)
    {
        if ((size_ + 1) * 2 > slots_.size()) {
            grow();
        }
        for (size_t i = hash(key) & mask_; ; i = (i + 1) & mask_) {
            Slot &slot = slots_[i];
            if (slot.key == key) {
                return slot.value;
            }
            if (slot.key == kNoPair) {
                slot.key = key;
                size_++;
                return slot.value;
            }
        }
    }

private:
    struct Slot {
        Pair key = kNoPair;
        V value = V();
    };

    static inline size_t hash(Pair key)
    {
        uint64_t h = key;
        h ^= h >> 33;
        h *= 0xFF51AFD7ED558CCDull;
        h ^= h >> 33;
        h *= 0xC4CEB9FE1A85EC53ull;
        h ^= h >> 33;
        return (size_t)h;
    }

    void grow()
    {
        std::vector<Slot> slots(slots_.empty() ? 16 : slots_.size() * 2);
        size_t mask = slots.size() - 1;
        for (const Slot &slot : slots_) {
            if (slot.key != kNoPair) {
                size_t i = hash(slot.key) & mask;
                while (slots[i].key != kNoPair) {
                    i = (i + 1) & mask;
                }
                slots[i] = slot;
            }
        }
        slots_.swap(slots);
        mask_ = mask;
    }

    std::vector<Slot> slots_;
    size_t mask_ = 0;
    size_t size_ = 0;
};

//

// A pattern and the merges learned for it. Shared, and so never changed, once a Tokenizer has been pointed at it.
struct Model {
    explicit Model(const Pcre2Capi *pcre2_capi) : capi(pcre2_capi) {}

    ~Model()
    {
        pcre2_match_data *match_data = spare_match_data.load(std::memory_order_relaxed);
        if (match_data != nullptr) {
            capi->match_data_free(match_data);
        }
        if (code != nullptr) {
            capi->code_free(code);
        }
    }

    Model(const Model &) = delete;
    Model & operator=(const Model &) = delete;

    const Pcre2Capi *const capi;

    std::string pattern;

    // Null for a Tokenizer which has never been trained, which has no pattern and so splits text into nothing.
    pcre2_code *code = nullptr;

    // Whether PCRE2 validates a text before matching code against it - and so whether a text it has validated once
    // can be spared that for the rest of a search.
    bool validates_utf = false;

    // In the order learned: merges[i] is the pair which makes token 256 + i.
    std::vector<Pair> merges;
    PairMap<uint32_t> merge_tokens;

    // The bytes of every token.
    std::vector<std::string> vocab;

    // A match data block for code which is not in use, if any. Each search needs one to itself for as long as it
    // runs, and making one costs enough to show when encoding short texts one at a time, so the last one finished
    // with is kept here for the next.
    mutable std::atomic<pcre2_match_data *> spare_match_data{nullptr};
};

// Fills in what of a model follows from its merges.
static void index_model(Model &model)
{
    model.vocab.reserve(256 + model.merges.size());
    for (int byte = 0; byte < 256; byte++) {
        model.vocab.emplace_back(1, (char)byte);
    }
    for (size_t i = 0; i < model.merges.size(); i++) {
        Pair pair = model.merges[i];
        model.merge_tokens[pair] = (uint32_t)(256 + i);
        std::string bytes = model.vocab[pair_left(pair)] + model.vocab[pair_right(pair)];
        model.vocab.push_back(std::move(bytes));
    }
}

//

// A model's match data block, taken for the life of this - its spare one if there is one, and otherwise a new one.
class MatchData {
public:
    explicit MatchData(const Model &model) : model_(model)
    {
        match_data_ = model.spare_match_data.exchange(nullptr, std::memory_order_acquire);
        if (match_data_ == nullptr) {
            match_data_ = model.capi->match_data_create_from_pattern(model.code, nullptr);
        }
    }

    ~MatchData()
    {
        if (match_data_ == nullptr) {
            return;
        }
        pcre2_match_data *expected = nullptr;
        if (!model_.spare_match_data.compare_exchange_strong(
            expected,
            match_data_,
            std::memory_order_release,
            std::memory_order_relaxed
        )) {
            model_.capi->match_data_free(match_data_);
        }
    }

    MatchData(const MatchData &) = delete;
    MatchData & operator=(const MatchData &) = delete;

    // Null if one could not be allocated.
    pcre2_match_data * get() const
    {
        return match_data_;
    }

private:
    const Model &model_;
    pcre2_match_data *match_data_;
};

// Hands fn each chunk the model's pattern splits text into, in order: each successive match of it which is not empty.
// Returns 0, or the PCRE2 error which stopped it. Text which is in no match is in no chunk, and is skipped.
//
// The search goes on from the end of each match as fancy-regex's does, which is not quite as Perl's and PCRE2's own
// do: after an empty match they look for one which is not empty in the same place, where this just moves on a
// character. It only shows for a pattern which can match nothing, which is not one anybody splits text with, but
// costs nothing to have the same.
template <typename F>
static int for_each_chunk(
    const Model &model,
    pcre2_match_context *match_context,
    pcre2_match_data *match_data,
    std::string_view text,
    F &&fn
)
{
    const Pcre2Capi *capi = model.capi;
    PCRE2_SIZE *ovector = capi->get_ovector_pointer(match_data);
    size_t offset = 0;
    uint32_t options = 0;

    while (offset <= text.size()) {
        int rc = capi->match(
            model.code,
            (PCRE2_SPTR)text.data(),
            (PCRE2_SIZE)text.size(),
            (PCRE2_SIZE)offset,
            options,
            match_data,
            match_context
        );
        if (rc == PCRE2_ERROR_NOMATCH) {
            return 0;
        }
        if (rc < 0) {
            return rc;
        }

        size_t start = ovector[0];
        size_t end = ovector[1];
        if (end > start) {
            fn(std::string_view(text.data() + start, end - start));
        }

        // Always onward, even from a match which somehow ends before the search for it began.
        if (end > start && end > offset) {
            offset = end;
        } else {
            offset = std::max(offset, end) + 1;
            while (offset < text.size() && ((uint8_t)text[offset] & 0xC0) == 0x80) {
                offset++;
            }
        }

        // Left to itself PCRE2 validates everything ahead of the offset on every call, making this loop quadratic in
        // the length of the text. The first call validated all of it, a str's UTF-8 cannot change, and with no \C in
        // the pattern no match ends, and so no search begins, anywhere but at the start of a character - which is all
        // that skipping the check needs.
        if (model.validates_utf) {
            options = PCRE2_NO_UTF_CHECK;
        }
    }

    return 0;
}

// Runs work(0) on this thread, and work(1) through work(num_workers - 1) each on one of its own, returning once all
// are done. work must not throw. Workers which cannot be started are not run at all, so the work has to be shared out
// such that those which are can do all of it.
template <typename F>
static void run_workers(size_t num_workers, F &&work)
{
    std::vector<std::thread> threads;
    try {
        threads.reserve(num_workers - 1);
        for (size_t worker = 1; worker < num_workers; worker++) {
            threads.emplace_back(std::ref(work), worker);
        }
    } catch (const std::exception &) {
    }
    work(0);
    for (std::thread &thread : threads) {
        thread.join();
    }
}

// How many workers to share out a number of texts of a total size between, given how many may be used.
static size_t plan_workers(size_t max_workers, size_t num_texts, size_t total_size)
{
    return std::max<size_t>(std::min({max_workers, num_texts, total_size / kWorkerSize}), 1);
}

//

struct ChunkHash {
    typedef void is_transparent;

    size_t operator()(std::string_view chunk) const noexcept
    {
        return std::hash<std::string_view>()(chunk);
    }
};

// How many times each distinct chunk has been seen.
typedef std::unordered_map<std::string, int64_t, ChunkHash, std::equal_to<>> ChunkCounts;

static int count_text_chunks(
    const Model &model,
    pcre2_match_context *match_context,
    pcre2_match_data *match_data,
    std::string_view text,
    ChunkCounts &counts
)
{
    return for_each_chunk(model, match_context, match_data, text, [&](std::string_view chunk) {
        auto it = counts.find(chunk);
        if (it != counts.end()) {
            it->second++;
        } else {
            counts.emplace(chunk, 1);
        }
    });
}

// Adds to counts the chunks the model's pattern splits texts into. The model and match context are shared by every
// worker, each of which has a match data block of its own. Returns 0, or the first error any worker hit.
static int count_chunks(
    const Model &model,
    pcre2_match_context *match_context,
    const std::vector<std::string_view> &texts,
    size_t num_workers,
    ChunkCounts &counts
)
{
    if (num_workers <= 1) {
        MatchData match_data(model);
        if (match_data.get() == nullptr) {
            return PCRE2_ERROR_NOMEMORY;
        }
        for (std::string_view text : texts) {
            int rc = count_text_chunks(model, match_context, match_data.get(), text, counts);
            if (rc < 0) {
                return rc;
            }
        }
        return 0;
    }

    std::vector<ChunkCounts> partials(num_workers);
    std::vector<int> errors(num_workers, 0);
    std::atomic<size_t> next_text{0};
    std::atomic<bool> failed{false};

    // Workers pull texts from a shared counter, so one which never starts only costs speed.
    auto work = [&](size_t worker) noexcept {
        try {
            MatchData match_data(model);
            if (match_data.get() == nullptr) {
                throw std::bad_alloc();
            }
            while (!failed.load(std::memory_order_relaxed)) {
                size_t i = next_text.fetch_add(1, std::memory_order_relaxed);
                if (i >= texts.size()) {
                    break;
                }
                int rc = count_text_chunks(model, match_context, match_data.get(), texts[i], partials[worker]);
                if (rc < 0) {
                    errors[worker] = rc;
                    failed.store(true, std::memory_order_relaxed);
                }
            }
        } catch (const std::exception &) {
            errors[worker] = PCRE2_ERROR_NOMEMORY;
            failed.store(true, std::memory_order_relaxed);
        }
    };
    run_workers(num_workers, work);

    for (int error : errors) {
        if (error < 0) {
            return error;
        }
    }

    for (ChunkCounts &partial : partials) {
        // Moves over every chunk counts does not have, leaving behind those it does.
        counts.merge(partial);
        for (const auto &[chunk, count] : partial) {
            counts.find(chunk)->second += count;
        }
    }
    return 0;
}

//

// A pair waiting to be merged: how often it occurred when last looked at, and which words it may occur in.
struct MergeJob {
    Pair pair;
    int64_t count;
    size_t words_start;
    size_t words_size;
};

// Orders the heap of jobs such that the most frequent pair is on top, and of those equally frequent the least.
static inline bool merge_job_less(const MergeJob &a, const MergeJob &b)
{
    if (a.count != b.count) {
        return a.count < b.count;
    }
    return a.pair > b.pair;
}

struct FreshPair {
    Pair pair;
    uint32_t word;
};

static inline bool fresh_pair_less(const FreshPair &a, const FreshPair &b)
{
    if (a.pair != b.pair) {
        return a.pair < b.pair;
    }
    return a.word < b.word;
}

// Learns up to num_merges merges from the chunks counted, which it consumes, appending the pairs merged to merges in
// the order they are. Every so often it calls poll, and stops if that returns true. Returns 0 or an error.
//
// This is rustbpe's train_core_incremental, and chooses as it does: always the most frequent pair, and of those
// equally frequent the least. Each distinct chunk is a word, held once and weighted by its count. Rather than
// recount, each merge adjusts the counts of just the pairs it makes and breaks, and each pair is queued along with the
// words it was seen in, so that merging it need only visit those. A count only ever falls once its pair is queued, so
// a job's count is trusted only as far as putting it on top of the heap: there it is checked, and if stale the job is
// requeued with the true one.
template <typename P>
static int train_merges(ChunkCounts &chunk_counts, uint64_t num_merges, P &&poll, std::vector<Pair> &merges)
{
    // Every word's tokens end to end. A word only ever shrinks, which it does in place. Words of a single token have
    // no pairs to offer, and are left out.
    std::vector<uint32_t> tokens;
    std::vector<size_t> word_starts;
    std::vector<size_t> word_sizes;
    std::vector<int64_t> word_counts;

    {
        size_t num_words = 0;
        size_t num_tokens = 0;
        for (const auto &[chunk, count] : chunk_counts) {
            if (chunk.size() >= 2) {
                num_words++;
                num_tokens += chunk.size();
            }
        }
        if (num_words >= kNoToken) {
            return kErrorTooManyChunks;
        }

        tokens.reserve(num_tokens);
        word_starts.reserve(num_words);
        word_sizes.reserve(num_words);
        word_counts.reserve(num_words);
        for (const auto &[chunk, count] : chunk_counts) {
            if (chunk.size() >= 2) {
                word_starts.push_back(tokens.size());
                word_sizes.push_back(chunk.size());
                word_counts.push_back(count);
                for (char byte : chunk) {
                    tokens.push_back((uint8_t)byte);
                }
            }
        }

        ChunkCounts().swap(chunk_counts);
    }

    uint32_t num_words = (uint32_t)word_starts.size();

    PairMap<int64_t> pair_counts;

    // The words of every job, each job's together, and in ascending order.
    std::vector<uint32_t> job_words;

    std::vector<MergeJob> heap;

    // To begin with every token is a byte, so the pairs can be counted, and their words gathered, in flat tables.
    {
        const size_t num_byte_pairs = 256 * 256;
        std::vector<int64_t> counts(num_byte_pairs, 0);
        std::vector<size_t> sizes(num_byte_pairs, 0);
        std::vector<size_t> ends(num_byte_pairs, 0);

        // One more than the last word each pair was seen in, by which a word is counted once for a pair however often
        // it has it.
        std::vector<uint32_t> seen(num_byte_pairs, 0);

        for (uint32_t word = 0; word < num_words; word++) {
            const uint32_t *word_tokens = tokens.data() + word_starts[word];
            for (size_t i = 0; i + 1 < word_sizes[word]; i++) {
                size_t byte_pair = ((size_t)word_tokens[i] << 8) | word_tokens[i + 1];
                counts[byte_pair] += word_counts[word];
                if (seen[byte_pair] != word + 1) {
                    seen[byte_pair] = word + 1;
                    sizes[byte_pair]++;
                }
            }
        }

        size_t total_size = 0;
        for (size_t byte_pair = 0; byte_pair < num_byte_pairs; byte_pair++) {
            ends[byte_pair] = total_size;
            total_size += sizes[byte_pair];
        }
        job_words.resize(total_size);

        std::fill(seen.begin(), seen.end(), 0);
        for (uint32_t word = 0; word < num_words; word++) {
            const uint32_t *word_tokens = tokens.data() + word_starts[word];
            for (size_t i = 0; i + 1 < word_sizes[word]; i++) {
                size_t byte_pair = ((size_t)word_tokens[i] << 8) | word_tokens[i + 1];
                if (seen[byte_pair] != word + 1) {
                    seen[byte_pair] = word + 1;
                    job_words[ends[byte_pair]++] = word;
                }
            }
        }

        for (size_t byte_pair = 0; byte_pair < num_byte_pairs; byte_pair++) {
            if (counts[byte_pair] > 0) {
                Pair pair = make_pair((uint32_t)(byte_pair >> 8), (uint32_t)(byte_pair & 0xFF));
                pair_counts[pair] = counts[byte_pair];
                heap.push_back(MergeJob{
                    .pair = pair,
                    .count = counts[byte_pair],
                    .words_start = ends[byte_pair] - sizes[byte_pair],
                    .words_size = sizes[byte_pair],
                });
            }
        }
        std::make_heap(heap.begin(), heap.end(), merge_job_less);
    }

    // The pairs a merge makes, each with the word it was made in.
    std::vector<FreshPair> fresh;

    // Long enough ago that the first merge polls: nothing has since the last of the text began to be split.
    std::chrono::steady_clock::time_point polled_at{};

    while (merges.size() < num_merges && !heap.empty()) {
        std::pop_heap(heap.begin(), heap.end(), merge_job_less);
        MergeJob top = heap.back();
        heap.pop_back();

        int64_t count = pair_counts[top.pair];
        if (count <= 0) {
            continue;
        }
        if (top.count != count) {
            top.count = count;
            heap.push_back(top);
            std::push_heap(heap.begin(), heap.end(), merge_job_less);
            continue;
        }

        uint32_t left = pair_left(top.pair);
        uint32_t right = pair_right(top.pair);
        uint32_t merged = (uint32_t)(256 + merges.size());
        merges.push_back(top.pair);

        // Replaces each occurrence of the pair, left to right, in each word it was seen in - not all of which need
        // still have it. Replacing one breaks the pairs it made with the tokens either side, and makes new ones with
        // them in their place.
        fresh.clear();
        for (size_t i = 0; i < top.words_size; i++) {
            uint32_t word = job_words[top.words_start + i];
            uint32_t *word_tokens = tokens.data() + word_starts[word];
            size_t size = word_sizes[word];
            int64_t word_count = word_counts[word];

            size_t out = 0;
            for (size_t in = 0; in < size; ) {
                if (in + 1 < size && word_tokens[in] == left && word_tokens[in + 1] == right) {
                    if (out > 0) {
                        uint32_t before = word_tokens[out - 1];
                        pair_counts[make_pair(before, left)] -= word_count;
                        pair_counts[make_pair(before, merged)] += word_count;
                        fresh.push_back(FreshPair{make_pair(before, merged), word});
                    }
                    pair_counts[top.pair] -= word_count;
                    if (in + 2 < size) {
                        uint32_t after = word_tokens[in + 2];
                        pair_counts[make_pair(right, after)] -= word_count;
                        pair_counts[make_pair(merged, after)] += word_count;
                        fresh.push_back(FreshPair{make_pair(merged, after), word});
                    }
                    word_tokens[out++] = merged;
                    in += 2;
                } else {
                    word_tokens[out++] = word_tokens[in++];
                }
            }
            word_sizes[word] = out;
        }

        // Queues each pair made. All of them hold the new token, so none has been queued before, and none can be made
        // again later: this is the one time each is seen.
        std::sort(fresh.begin(), fresh.end(), fresh_pair_less);
        for (size_t i = 0; i < fresh.size(); ) {
            Pair pair = fresh[i].pair;
            size_t words_start = job_words.size();
            for (; i < fresh.size() && fresh[i].pair == pair; i++) {
                if (job_words.size() == words_start || job_words.back() != fresh[i].word) {
                    job_words.push_back(fresh[i].word);
                }
            }

            // A pair made by one replacement is broken by the next if that comes straight after it - as it does where
            // the pair being merged repeats - and so can come out of this with nothing to its name.
            int64_t pair_count = pair_counts[pair];
            if (pair_count > 0) {
                heap.push_back(MergeJob{
                    .pair = pair,
                    .count = pair_count,
                    .words_start = words_start,
                    .words_size = job_words.size() - words_start,
                });
                std::push_heap(heap.begin(), heap.end(), merge_job_less);
            } else {
                job_words.resize(words_start);
            }
        }

        auto now = std::chrono::steady_clock::now();
        if (now - polled_at >= kPollInterval) {
            if (poll()) {
                return kErrorInterrupted;
            }
            polled_at = std::chrono::steady_clock::now();
        }
    }

    return 0;
}

//

// What a text is encoded with, kept from one chunk to the next to spare allocating it for each.
struct EncodeScratch {
    std::vector<uint32_t> tokens;
    std::vector<uint32_t> ranks;

    struct Candidate {
        uint32_t rank;
        size_t at;
    };

    std::vector<size_t> befores;
    std::vector<size_t> afters;
    std::vector<Candidate> heap;
};

// The token a pair of tokens merges into, which doubles as the order in which merges apply: the lower the earlier it
// was learned, and so the sooner it is applied. kNoToken, which orders after them all, if the pair does not merge.
static inline uint32_t merge_rank(const Model &model, uint32_t left, uint32_t right)
{
    const uint32_t *token = model.merge_tokens.find(make_pair(left, right));
    return token != nullptr ? *token : kNoToken;
}

// Appends the tokens of a chunk to out. As rustbpe does, it takes the pair which merges earliest, and of those the
// first, merges it, and starts again - only keeping each pair's rank rather than looking them all up again each time.
static void encode_chunk(const Model &model, std::string_view chunk, EncodeScratch &scratch, std::vector<uint32_t> &out)
{
    size_t size = chunk.size();
    scratch.tokens.resize(size);
    scratch.ranks.resize(size);
    uint32_t *tokens = scratch.tokens.data();
    uint32_t *ranks = scratch.ranks.data();

    for (size_t i = 0; i < size; i++) {
        tokens[i] = (uint8_t)chunk[i];
    }

    // ranks[i] is that of the pair of tokens at i and i + 1.
    for (size_t i = 0; i + 1 < size; i++) {
        ranks[i] = merge_rank(model, tokens[i], tokens[i + 1]);
    }

    while (size >= 2) {
        uint32_t rank = kNoToken;
        size_t at = 0;
        for (size_t i = 0; i + 1 < size; i++) {
            if (ranks[i] < rank) {
                rank = ranks[i];
                at = i;
            }
        }
        if (rank == kNoToken) {
            break;
        }

        tokens[at] = rank;
        std::memmove(tokens + at + 1, tokens + at + 2, (size - at - 2) * sizeof(uint32_t));
        std::memmove(ranks + at + 1, ranks + at + 2, (size - at - 2) * sizeof(uint32_t));
        size--;

        if (at > 0) {
            ranks[at - 1] = merge_rank(model, tokens[at - 1], tokens[at]);
        }
        if (at + 1 < size) {
            ranks[at] = merge_rank(model, tokens[at], tokens[at + 1]);
        }
    }

    out.insert(out.end(), tokens, tokens + size);
}

// Orders the heap of candidates such that the one which merges earliest is on top, and of those the first.
static inline bool candidate_greater(const EncodeScratch::Candidate &a, const EncodeScratch::Candidate &b)
{
    if (a.rank != b.rank) {
        return a.rank > b.rank;
    }
    return a.at > b.at;
}

// encode_chunk for a long chunk: it merges the same pairs in the same order, but finding each takes it time in the
// logarithm of the chunk's length where encode_chunk takes time in the length itself - which over a chunk of a
// megabyte, as a genome written out in letters is, is the difference between a moment and hours.
//
// The tokens stay where they start out, linked each to those either side of it, with a merge keeping the left of its
// two and unlinking the right. Mergeable pairs are queued by rank, then position, as they appear. Those that have
// since gone are not removed from the queue, but are recognised when they reach the top of it: a rank is that of one
// pair only, so a candidate still stands if that is still the pair it finds where it points.
static void encode_long_chunk(
    const Model &model,
    std::string_view chunk,
    EncodeScratch &scratch,
    std::vector<uint32_t> &out
)
{
    size_t size = chunk.size();
    scratch.tokens.resize(size);
    scratch.befores.resize(size);
    scratch.afters.resize(size);
    uint32_t *tokens = scratch.tokens.data();
    size_t *befores = scratch.befores.data();
    size_t *afters = scratch.afters.data();
    std::vector<EncodeScratch::Candidate> &heap = scratch.heap;

    // A token's neighbours are given by index, with size for none.
    for (size_t i = 0; i < size; i++) {
        tokens[i] = (uint8_t)chunk[i];
        befores[i] = (i > 0) ? i - 1 : size;
        afters[i] = i + 1;
    }

    heap.clear();
    for (size_t i = 0; i + 1 < size; i++) {
        uint32_t rank = merge_rank(model, tokens[i], tokens[i + 1]);
        if (rank != kNoToken) {
            heap.push_back(EncodeScratch::Candidate{rank, i});
        }
    }
    std::make_heap(heap.begin(), heap.end(), candidate_greater);

    while (!heap.empty()) {
        std::pop_heap(heap.begin(), heap.end(), candidate_greater);
        EncodeScratch::Candidate top = heap.back();
        heap.pop_back();

        size_t at = top.at;
        size_t after = afters[at];
        Pair pair = model.merges[top.rank - 256];
        if (after == size || tokens[at] != pair_left(pair) || tokens[after] != pair_right(pair)) {
            continue;
        }

        // An unlinked token is left as no token, which no candidate pointing at it can then find its pair in.
        tokens[at] = top.rank;
        tokens[after] = kNoToken;
        size_t next = afters[after];
        afters[at] = next;
        if (next != size) {
            befores[next] = at;
        }

        size_t before = befores[at];
        if (before != size) {
            uint32_t rank = merge_rank(model, tokens[before], tokens[at]);
            if (rank != kNoToken) {
                heap.push_back(EncodeScratch::Candidate{rank, before});
                std::push_heap(heap.begin(), heap.end(), candidate_greater);
            }
        }
        if (next != size) {
            uint32_t rank = merge_rank(model, tokens[at], tokens[next]);
            if (rank != kNoToken) {
                heap.push_back(EncodeScratch::Candidate{rank, at});
                std::push_heap(heap.begin(), heap.end(), candidate_greater);
            }
        }
    }

    for (size_t i = 0; i != size; i = afters[i]) {
        out.push_back(tokens[i]);
    }
}

// Appends the tokens of a text to out. Returns 0, or the PCRE2 error which stopped it.
static int encode_text(
    const Model &model,
    pcre2_match_context *match_context,
    pcre2_match_data *match_data,
    std::string_view text,
    EncodeScratch &scratch,
    std::vector<uint32_t> &out
)
{
    return for_each_chunk(model, match_context, match_data, text, [&](std::string_view chunk) {
        if (chunk.size() == 1) {
            out.push_back((uint8_t)chunk[0]);
        } else if (chunk.size() <= kLongChunkSize) {
            encode_chunk(model, chunk, scratch, out);
        } else {
            encode_long_chunk(model, chunk, scratch, out);
        }
    });
}

// Encodes each of num_texts texts into the vector of outs matching it, which must start out empty. Returns 0, or the
// first error any worker hit.
static int encode_texts(
    const Model &model,
    pcre2_match_context *match_context,
    const std::string_view *texts,
    size_t num_texts,
    size_t num_workers,
    std::vector<uint32_t> *outs
)
{
    if (model.code == nullptr) {
        return 0;
    }

    if (num_workers <= 1) {
        MatchData match_data(model);
        if (match_data.get() == nullptr) {
            return PCRE2_ERROR_NOMEMORY;
        }
        EncodeScratch scratch;
        for (size_t i = 0; i < num_texts; i++) {
            int rc = encode_text(model, match_context, match_data.get(), texts[i], scratch, outs[i]);
            if (rc < 0) {
                return rc;
            }
        }
        return 0;
    }

    std::vector<int> errors(num_workers, 0);
    std::atomic<size_t> next_text{0};
    std::atomic<bool> failed{false};

    auto work = [&](size_t worker) noexcept {
        try {
            MatchData match_data(model);
            if (match_data.get() == nullptr) {
                throw std::bad_alloc();
            }
            EncodeScratch scratch;
            while (!failed.load(std::memory_order_relaxed)) {
                size_t i = next_text.fetch_add(1, std::memory_order_relaxed);
                if (i >= num_texts) {
                    break;
                }
                int rc = encode_text(model, match_context, match_data.get(), texts[i], scratch, outs[i]);
                if (rc < 0) {
                    errors[worker] = rc;
                    failed.store(true, std::memory_order_relaxed);
                }
            }
        } catch (const std::exception &) {
            errors[worker] = PCRE2_ERROR_NOMEMORY;
            failed.store(true, std::memory_order_relaxed);
        }
    };
    run_workers(num_workers, work);

    for (int error : errors) {
        if (error < 0) {
            return error;
        }
    }
    return 0;
}

//

typedef struct bpe_state {
    PyTypeObject *TokenizerType;

    const Pcre2Capi *capi;

    // Shared by all short work, and never changed.
    pcre2_match_context *probe_match_context;
} bpe_state;

static inline bpe_state * get_bpe_state(PyObject *module)
{
    void *state = PyModule_GetState(module);
    assert(state != nullptr);
    return (bpe_state *)state;
}

//

// Runs fn with the thread state attached, as it is, turning anything it throws into an error.
template <typename F>
static int attached(F &&fn) noexcept
{
    try {
        return fn();
    } catch (const std::exception &) {
        return PCRE2_ERROR_NOMEMORY;
    }
}

// Runs fn with the thread state detached, turning anything it throws into an error: nothing may be thrown past the
// point the thread state is reattached at. fn must touch no Python object.
template <typename F>
static int detached(F &&fn) noexcept
{
    PyThreadState *thread_state = PyEval_SaveThread();
    int rc = attached(fn);
    PyEval_RestoreThread(thread_state);
    return rc;
}

// Runs work of a given size, as fn(match_context): attached and under the probe's limit if short, and detached
// otherwise or if that limit is hit - in which case fn is run a second time, and has to cope with having been stopped
// partway through the first.
template <typename F>
static int run_work(bpe_state *state, size_t size, F &&fn) noexcept
{
    if (size < kDetachSize) {
        int rc = attached([&]() {
            return fn(state->probe_match_context);
        });
        if (rc != PCRE2_ERROR_MATCHLIMIT) {
            return rc;
        }
    }
    return detached([&]() {
        return fn((pcre2_match_context *)nullptr);
    });
}

// Sets the exception for an error returned by the above, unless it is one which comes with it already set.
static void set_error(const Pcre2Capi *capi, int rc)
{
    if (rc == kErrorInterrupted) {
        assert(PyErr_Occurred());
        return;
    }
    if (rc == PCRE2_ERROR_NOMEMORY) {
        PyErr_NoMemory();
        return;
    }
    if (rc == kErrorTooManyChunks) {
        PyErr_SetString(PyExc_OverflowError, "too many distinct chunks to train on");
        return;
    }

    PCRE2_UCHAR message[256];
    if (capi->get_error_message(rc, message, sizeof(message)) == PCRE2_ERROR_BADDATA) {
        PyErr_Format(PyExc_RuntimeError, "regex match failed: PCRE2 error %d", rc);
    } else {
        PyErr_Format(PyExc_RuntimeError, "regex match failed: %s", (const char *)message);
    }
}

// Reads an optional number of threads, which absent is as many as there are cores. Returns false with an exception
// set if it is not one.
static bool parse_num_threads(PyObject *obj, size_t *out)
{
    if (obj == nullptr || obj == Py_None) {
        unsigned int num_cores = std::thread::hardware_concurrency();
        *out = std::clamp<size_t>(num_cores, 1, (size_t)kMaxThreads);
        return true;
    }

    long long num_threads = PyLong_AsLongLong(obj);
    if (num_threads == -1 && PyErr_Occurred()) {
        return false;
    }
    if (num_threads < 1 || num_threads > kMaxThreads) {
        PyErr_Format(PyExc_ValueError, "num_threads must be between 1 and %lld", kMaxThreads);
        return false;
    }
    *out = (size_t)num_threads;
    return true;
}

// The UTF-8 of a str, which is cached on it and is as immutable as it is: the view stays good, with or without a
// thread state attached, for as long as a reference to the str is held. Returns false with an exception set if obj is
// not a str, or is one which cannot be encoded.
static bool get_text(PyObject *obj, std::string_view *out)
{
    if (!PyUnicode_Check(obj)) {
        PyErr_Format(PyExc_TypeError, "expected str, got %T", obj);
        return false;
    }
    Py_ssize_t size = 0;
    const char *data = PyUnicode_AsUTF8AndSize(obj, &size);
    if (data == nullptr) {
        return false;
    }
    *out = std::string_view(data, (size_t)size);
    return true;
}

// Compiles a pattern into a new model with no merges. Returns null with an exception set if it cannot be.
static std::shared_ptr<Model> make_model(const Pcre2Capi *capi, std::string_view pattern)
{
    std::shared_ptr<Model> model;
    try {
        model = std::make_shared<Model>(capi);
        model->pattern = pattern;
    } catch (const std::exception &) {
        PyErr_NoMemory();
        return nullptr;
    }

    int error_code = 0;
    PCRE2_SIZE error_offset = 0;
    model->code = capi->compile(
        (PCRE2_SPTR)pattern.data(),
        (PCRE2_SIZE)pattern.size(),
        kCompileOptions,
        &error_code,
        &error_offset,
        nullptr
    );
    if (model->code == nullptr) {
        PCRE2_UCHAR message[256];
        if (capi->get_error_message(error_code, message, sizeof(message)) == PCRE2_ERROR_BADDATA) {
            PyErr_Format(PyExc_ValueError, "Invalid regex pattern: PCRE2 error %d", error_code);
        } else {
            PyErr_Format(
                PyExc_ValueError,
                "Invalid regex pattern: %s at offset %zu",
                (const char *)message,
                (size_t)error_offset
            );
        }
        return nullptr;
    }

    uint32_t all_options = 0;
    capi->pattern_info(model->code, PCRE2_INFO_ALLOPTIONS, &all_options);
    model->validates_utf = (all_options & PCRE2_UTF) != 0 && (all_options & PCRE2_MATCH_INVALID_UTF) == 0;

    return model;
}

static PyObject * tokens_to_list(const std::vector<uint32_t> &tokens)
{
    PyObject *list = PyList_New((Py_ssize_t)tokens.size());
    if (list == nullptr) {
        return nullptr;
    }
    for (size_t i = 0; i < tokens.size(); i++) {
        PyObject *item = PyLong_FromUnsignedLong(tokens[i]);
        if (item == nullptr) {
            Py_DECREF(list);
            return nullptr;
        }
        PyList_SET_ITEM(list, (Py_ssize_t)i, item);
    }
    return list;
}

// The one argument of a method which takes exactly that, whether given by position or by name. Returns null with an
// exception set if given anything else.
static PyObject * parse_only_arg(
    PyObject *const *args,
    Py_ssize_t nargs,
    PyObject *kwnames,
    const char *method_name,
    const char *arg_name
)
{
    Py_ssize_t nkwargs = (kwnames != nullptr) ? PyTuple_GET_SIZE(kwnames) : 0;
    if (nargs == 1 && nkwargs == 0) {
        return args[0];
    }
    if (nargs == 0 && nkwargs == 1 && PyUnicode_CompareWithASCIIString(PyTuple_GET_ITEM(kwnames, 0), arg_name) == 0) {
        return args[0];
    }
    PyErr_Format(PyExc_TypeError, "%s() takes exactly one argument, '%s'", method_name, arg_name);
    return nullptr;
}

//

typedef struct Tokenizer {
    PyObject_HEAD

    // Held only for as long as it takes to copy or replace model, which is what it guards.
    PyMutex mutex;
    std::shared_ptr<const Model> model;
} Tokenizer;

static inline bpe_state * Tokenizer_get_state(Tokenizer *self)
{
    void *state = PyType_GetModuleState(Py_TYPE(self));
    assert(state != nullptr);
    return (bpe_state *)state;
}

// The model as it stands, which whoever asks then shares in owning: it stays as it is, and alive, for as long as they
// hold it, whatever becomes of the Tokenizer in the meantime.
static std::shared_ptr<const Model> Tokenizer_get_model(Tokenizer *self)
{
    PyMutex_Lock(&self->mutex);
    std::shared_ptr<const Model> model = self->model;
    PyMutex_Unlock(&self->mutex);
    return model;
}

static void Tokenizer_set_model(Tokenizer *self, std::shared_ptr<const Model> model)
{
    PyMutex_Lock(&self->mutex);
    self->model.swap(model);
    PyMutex_Unlock(&self->mutex);
}

static PyObject * Tokenizer_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    if (PyTuple_GET_SIZE(args) != 0 || (kwargs != nullptr && PyDict_GET_SIZE(kwargs) != 0)) {
        PyErr_SetString(PyExc_TypeError, "Tokenizer() takes no arguments");
        return nullptr;
    }

    bpe_state *state = (bpe_state *)PyType_GetModuleState(type);
    assert(state != nullptr);

    std::shared_ptr<Model> model;
    try {
        model = std::make_shared<Model>(state->capi);
        index_model(*model);
    } catch (const std::exception &) {
        return PyErr_NoMemory();
    }

    // Tracked only once whole.
    Tokenizer *self = PyObject_GC_New(Tokenizer, type);
    if (self == nullptr) {
        return nullptr;
    }
    self->mutex = PyMutex{};
    new (&self->model) std::shared_ptr<const Model>(std::move(model));
    PyObject_GC_Track((PyObject *)self);
    return (PyObject *)self;
}

static int Tokenizer_traverse(Tokenizer *self, visitproc visit, void *arg)
{
    Py_VISIT(Py_TYPE(self));
    return 0;
}

static void Tokenizer_dealloc(Tokenizer *self)
{
    PyObject_GC_UnTrack((PyObject *)self);
    self->model.~shared_ptr();
    PyTypeObject *type = Py_TYPE(self);
    type->tp_free((PyObject *)self);
    Py_DECREF(type);
}

//

// Counts into counts the chunks of everything iterator yields, taking buffer_size texts from it at a time. Returns 0,
// or -1 with an exception set.
static int Tokenizer_ingest(
    bpe_state *state,
    const Model &model,
    PyObject *iterator,
    size_t buffer_size,
    size_t num_threads,
    ChunkCounts &counts
)
{
    // The strs taken from the iterator, held on to keep the views of their UTF-8 good while they are read from.
    std::vector<PyObject *> held;
    std::vector<std::string_view> texts;

    int result = 0;
    bool exhausted = false;
    while (result == 0 && !exhausted) {
        // Not after the last of the text too, as training itself checks - and at once.
        if (PyErr_CheckSignals() < 0) {
            result = -1;
            break;
        }

        size_t total_size = 0;
        while (result == 0 && texts.size() < buffer_size) {
            PyObject *item = nullptr;
            int found = PyIter_NextItem(iterator, &item);
            if (found < 0) {
                result = -1;
                break;
            }
            if (found == 0) {
                exhausted = true;
                break;
            }

            std::string_view text;
            if (!get_text(item, &text)) {
                Py_DECREF(item);
                result = -1;
                break;
            }
            int rc = attached([&]() {
                texts.push_back(text);
                held.push_back(item);
                return 0;
            });
            if (rc < 0) {
                Py_DECREF(item);
                PyErr_NoMemory();
                result = -1;
                break;
            }
            total_size += text.size();
        }

        if (result == 0 && !texts.empty()) {
            int rc = run_work(state, total_size, [&](pcre2_match_context *match_context) {
                if (match_context == nullptr) {
                    size_t num_workers = plan_workers(num_threads, texts.size(), total_size);
                    return count_chunks(model, match_context, texts, num_workers, counts);
                }

                // Counted apart, so as to leave nothing behind should this be stopped short and done again.
                ChunkCounts partial;
                int partial_rc = count_chunks(model, match_context, texts, 1, partial);
                if (partial_rc < 0) {
                    return partial_rc;
                }
                for (const auto &[chunk, count] : partial) {
                    counts[chunk] += count;
                }
                return 0;
            });
            if (rc < 0) {
                set_error(state->capi, rc);
                result = -1;
            }
        }

        texts.clear();
        for (PyObject *item : held) {
            Py_DECREF(item);
        }
        held.clear();
    }

    return result;
}

PyDoc_STRVAR(
    Tokenizer_train_from_iterator_doc,
    "train_from_iterator(iterator, vocab_size, buffer_size=8192, pattern=None, *, num_threads=None)\n\n"
    "Learns the vocab_size - 256 merges, or as many as there are to learn, of the texts an iterator of strs yields, "
    "split by pattern - by default GPT4_PATTERN. The texts are taken buffer_size at a time, and split on up to "
    "num_threads threads - by default one per core. Replaces the pattern and any merges the tokenizer already had, "
    "but only once done: until then, and if it raises, the tokenizer is as it was."
);

static PyObject * Tokenizer_train_from_iterator(Tokenizer *self, PyObject *args, PyObject *kwargs)
{
    bpe_state *state = Tokenizer_get_state(self);

    static const char * const kwlist[] = {
        "iterator",
        "vocab_size",
        "buffer_size",
        "pattern",
        "num_threads",
        nullptr,
    };
    PyObject *iterable;
    long long vocab_size;
    Py_ssize_t buffer_size = 8192;
    PyObject *pattern_obj = Py_None;
    PyObject *num_threads_obj = Py_None;
    if (!PyArg_ParseTupleAndKeywords(
        args,
        kwargs,
        "OL|nO$O:train_from_iterator",
        kwlist,
        &iterable,
        &vocab_size,
        &buffer_size,
        &pattern_obj,
        &num_threads_obj
    )) {
        return nullptr;
    }

    if (vocab_size < 256 || vocab_size > kMaxVocabSize) {
        PyErr_Format(PyExc_ValueError, "vocab_size must be at least 256, and at most %lld", kMaxVocabSize);
        return nullptr;
    }
    if (buffer_size < 1) {
        PyErr_SetString(PyExc_ValueError, "buffer_size must be at least 1");
        return nullptr;
    }
    std::string_view pattern = GPT4_PATTERN;
    if (pattern_obj != Py_None && !get_text(pattern_obj, &pattern)) {
        return nullptr;
    }
    size_t num_threads = 1;
    if (!parse_num_threads(num_threads_obj, &num_threads)) {
        return nullptr;
    }

    // The pattern is compiled before anything is taken from the iterator, so that a bad one costs the caller nothing.
    std::shared_ptr<Model> model = make_model(state->capi, pattern);
    if (model == nullptr) {
        return nullptr;
    }

    PyObject *iterator = PyObject_GetIter(iterable);
    if (iterator == nullptr) {
        return nullptr;
    }
    ChunkCounts counts;
    int result = Tokenizer_ingest(state, *model, iterator, (size_t)buffer_size, num_threads, counts);
    Py_DECREF(iterator);
    if (result < 0) {
        return nullptr;
    }

    // Detached, but reattaching every so often to see if a signal has come in asking it to stop.
    PyThreadState *thread_state = PyEval_SaveThread();
    int rc = attached([&]() {
        auto poll = [&]() noexcept {
            PyEval_RestoreThread(thread_state);
            int signalled = PyErr_CheckSignals();
            thread_state = PyEval_SaveThread();
            return signalled < 0;
        };
        int train_rc = train_merges(counts, (uint64_t)(vocab_size - 256), poll, model->merges);
        if (train_rc < 0) {
            return train_rc;
        }
        index_model(*model);
        return 0;
    });
    PyEval_RestoreThread(thread_state);
    if (rc < 0) {
        set_error(state->capi, rc);
        return nullptr;
    }

    Tokenizer_set_model(self, std::move(model));
    Py_RETURN_NONE;
}

PyDoc_STRVAR(Tokenizer_get_pattern_doc, "get_pattern()\n\nThe pattern text is split by: empty until trained.");

static PyObject * Tokenizer_get_pattern(Tokenizer *self, PyObject *Py_UNUSED(ignored))
{
    std::shared_ptr<const Model> model = Tokenizer_get_model(self);
    return PyUnicode_FromStringAndSize(model->pattern.data(), (Py_ssize_t)model->pattern.size());
}

PyDoc_STRVAR(Tokenizer_vocab_size_doc, "The number of tokens: the 256 bytes, and one for each merge learned.");

static PyObject * Tokenizer_get_vocab_size(Tokenizer *self, void *Py_UNUSED(closure))
{
    std::shared_ptr<const Model> model = Tokenizer_get_model(self);
    return PyLong_FromSize_t(model->vocab.size());
}

PyDoc_STRVAR(
    Tokenizer_get_mergeable_ranks_doc,
    "get_mergeable_ranks()\n\n"
    "The bytes of every token paired with the token, in order: the form tiktoken takes a vocabulary in."
);

static PyObject * Tokenizer_get_mergeable_ranks(Tokenizer *self, PyObject *Py_UNUSED(ignored))
{
    std::shared_ptr<const Model> model = Tokenizer_get_model(self);

    PyObject *list = PyList_New((Py_ssize_t)model->vocab.size());
    if (list == nullptr) {
        return nullptr;
    }
    for (size_t token = 0; token < model->vocab.size(); token++) {
        const std::string &bytes = model->vocab[token];
        PyObject *item = Py_BuildValue("(y#n)", bytes.data(), (Py_ssize_t)bytes.size(), (Py_ssize_t)token);
        if (item == nullptr) {
            Py_DECREF(list);
            return nullptr;
        }
        PyList_SET_ITEM(list, (Py_ssize_t)token, item);
    }
    return list;
}

PyDoc_STRVAR(
    Tokenizer_encode_doc,
    "encode(text)\n\n"
    "The tokens of a str: of each chunk the pattern splits it into, with the merges learned applied in the order they "
    "were learned. Text the pattern does not match is in no chunk, and is left out."
);

static PyObject * Tokenizer_encode(Tokenizer *self, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
{
    bpe_state *state = Tokenizer_get_state(self);

    PyObject *text_obj = parse_only_arg(args, nargs, kwnames, "encode", "text");
    std::string_view text;
    if (text_obj == nullptr || !get_text(text_obj, &text)) {
        return nullptr;
    }

    std::shared_ptr<const Model> model = Tokenizer_get_model(self);

    std::vector<uint32_t> tokens;
    int rc = run_work(state, text.size(), [&](pcre2_match_context *match_context) {
        tokens.clear();
        return encode_texts(*model, match_context, &text, 1, 1, &tokens);
    });
    if (rc < 0) {
        set_error(state->capi, rc);
        return nullptr;
    }
    return tokens_to_list(tokens);
}

PyDoc_STRVAR(
    Tokenizer_batch_encode_doc,
    "batch_encode(texts, *, num_threads=None)\n\n"
    "The tokens of each of an iterable of strs, as encode gives them, encoded on up to num_threads threads - by "
    "default one per core."
);

static PyObject * Tokenizer_batch_encode(Tokenizer *self, PyObject *args, PyObject *kwargs)
{
    bpe_state *state = Tokenizer_get_state(self);

    static const char * const kwlist[] = {"texts", "num_threads", nullptr};
    PyObject *texts_obj;
    PyObject *num_threads_obj = Py_None;
    if (!PyArg_ParseTupleAndKeywords(
        args,
        kwargs,
        "O|$O:batch_encode",
        kwlist,
        &texts_obj,
        &num_threads_obj
    )) {
        return nullptr;
    }

    size_t num_threads = 1;
    if (!parse_num_threads(num_threads_obj, &num_threads)) {
        return nullptr;
    }

    // A str is an iterable of strs, and one given here is far likelier a mistake than a batch of single characters.
    if (PyUnicode_Check(texts_obj)) {
        PyErr_SetString(PyExc_TypeError, "texts must be an iterable of str, not a str");
        return nullptr;
    }

    // A tuple of its own is what keeps every text in place while they are read from with no thread state attached:
    // nothing else can take an item out of it.
    PyObject *texts_tuple = PySequence_Tuple(texts_obj);
    if (texts_tuple == nullptr) {
        return nullptr;
    }
    size_t num_texts = (size_t)PyTuple_GET_SIZE(texts_tuple);

    std::shared_ptr<const Model> model = Tokenizer_get_model(self);

    std::vector<std::string_view> texts;
    std::vector<std::vector<uint32_t>> outs;
    PyObject *result = nullptr;

    int rc = attached([&]() {
        texts.resize(num_texts);
        outs.resize(num_texts);
        return 0;
    });
    if (rc < 0) {
        PyErr_NoMemory();
        goto done;
    }

    {
        size_t total_size = 0;
        for (size_t i = 0; i < num_texts; i++) {
            if (!get_text(PyTuple_GET_ITEM(texts_tuple, (Py_ssize_t)i), &texts[i])) {
                goto done;
            }
            total_size += texts[i].size();
        }

        rc = run_work(state, total_size, [&](pcre2_match_context *match_context) {
            for (std::vector<uint32_t> &out : outs) {
                out.clear();
            }
            size_t num_workers = (match_context == nullptr) ? plan_workers(num_threads, num_texts, total_size) : 1;
            return encode_texts(*model, match_context, texts.data(), num_texts, num_workers, outs.data());
        });
        if (rc < 0) {
            set_error(state->capi, rc);
            goto done;
        }
    }

    result = PyList_New((Py_ssize_t)num_texts);
    if (result == nullptr) {
        goto done;
    }
    for (size_t i = 0; i < num_texts; i++) {
        PyObject *item = tokens_to_list(outs[i]);
        if (item == nullptr) {
            Py_CLEAR(result);
            goto done;
        }
        PyList_SET_ITEM(result, (Py_ssize_t)i, item);
    }

done:
    Py_DECREF(texts_tuple);
    return result;
}

PyDoc_STRVAR(
    Tokenizer_decode_doc,
    "decode(ids)\n\n"
    "The str an iterable of tokens encodes. Raises ValueError for one which is not a token, and UnicodeDecodeError if "
    "their bytes together are not UTF-8 - as those of tokens which do not together make up whole characters are not."
);

static PyObject * Tokenizer_decode(Tokenizer *self, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
{
    PyObject *ids_obj = parse_only_arg(args, nargs, kwnames, "decode", "ids");
    if (ids_obj == nullptr) {
        return nullptr;
    }

    // A str is an iterable too, though of nothing which could be a token.
    if (PyUnicode_Check(ids_obj)) {
        PyErr_SetString(PyExc_TypeError, "ids must be an iterable of int, not a str");
        return nullptr;
    }

    // A tuple of its own is one whose items nothing else can replace partway through this.
    PyObject *ids_tuple = PySequence_Tuple(ids_obj);
    if (ids_tuple == nullptr) {
        return nullptr;
    }
    Py_ssize_t num_ids = PyTuple_GET_SIZE(ids_tuple);

    std::shared_ptr<const Model> model = Tokenizer_get_model(self);

    std::string bytes;
    PyObject *result = nullptr;

    for (Py_ssize_t i = 0; i < num_ids; i++) {
        PyObject *item = PyTuple_GET_ITEM(ids_tuple, i);

        int overflow = 0;
        long long token = PyLong_AsLongLongAndOverflow(item, &overflow);
        if (token == -1 && PyErr_Occurred()) {
            goto done;
        }
        if (overflow != 0 || token < 0 || (unsigned long long)token >= model->vocab.size()) {
            PyErr_Format(PyExc_ValueError, "Unknown token id: %S", item);
            goto done;
        }

        int rc = attached([&]() {
            bytes += model->vocab[(size_t)token];
            return 0;
        });
        if (rc < 0) {
            PyErr_NoMemory();
            goto done;
        }
    }

    result = PyUnicode_DecodeUTF8(bytes.data(), (Py_ssize_t)bytes.size(), "strict");

done:
    Py_DECREF(ids_tuple);
    return result;
}

static PyMethodDef Tokenizer_methods[] = {
    {
        "train_from_iterator",
        (PyCFunction)(void (*)(void))Tokenizer_train_from_iterator,
        METH_VARARGS | METH_KEYWORDS,
        Tokenizer_train_from_iterator_doc,
    },
    {"get_pattern", (PyCFunction)Tokenizer_get_pattern, METH_NOARGS, Tokenizer_get_pattern_doc},
    {
        "get_mergeable_ranks",
        (PyCFunction)Tokenizer_get_mergeable_ranks,
        METH_NOARGS,
        Tokenizer_get_mergeable_ranks_doc,
    },
    {
        "encode",
        (PyCFunction)(void (*)(void))Tokenizer_encode,
        METH_FASTCALL | METH_KEYWORDS,
        Tokenizer_encode_doc,
    },
    {
        "batch_encode",
        (PyCFunction)(void (*)(void))Tokenizer_batch_encode,
        METH_VARARGS | METH_KEYWORDS,
        Tokenizer_batch_encode_doc,
    },
    {
        "decode",
        (PyCFunction)(void (*)(void))Tokenizer_decode,
        METH_FASTCALL | METH_KEYWORDS,
        Tokenizer_decode_doc,
    },
    {nullptr, nullptr, 0, nullptr}
};

static PyGetSetDef Tokenizer_getset[] = {
    {"vocab_size", (getter)Tokenizer_get_vocab_size, nullptr, Tokenizer_vocab_size_doc, nullptr},
    {nullptr, nullptr, nullptr, nullptr, nullptr}
};

PyDoc_STRVAR(
    Tokenizer_doc,
    "Tokenizer()\n\n"
    "A byte pair encoding tokenizer: untrained, it has no pattern, no merges, and encodes everything to nothing."
);

static PyType_Slot Tokenizer_slots[] = {
    {Py_tp_doc, (void *)Tokenizer_doc},
    {Py_tp_new, (void *)Tokenizer_new},
    {Py_tp_dealloc, (void *)Tokenizer_dealloc},
    {Py_tp_traverse, (void *)Tokenizer_traverse},
    {Py_tp_methods, (void *)Tokenizer_methods},
    {Py_tp_getset, (void *)Tokenizer_getset},
    {0, nullptr}
};

static PyType_Spec Tokenizer_spec = {
    .name = _MODULE_FULL_NAME ".Tokenizer",
    .basicsize = sizeof(Tokenizer),
    .itemsize = 0,
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_IMMUTABLETYPE,
    .slots = Tokenizer_slots,
};

//

PyDoc_STRVAR(bpe_doc, "A byte pair encoding trainer and encoder in the style of GPT-4's tokenizer");

static int bpe_exec(PyObject *module)
{
    bpe_state *state = get_bpe_state(module);

    // PyCapsule_Import walks the dotted name by attribute access, which finds a submodule only once something has
    // imported it - so that has to be done here first, or this module would only load after _pcre2 happened to.
    PyObject *pcre2_module = PyImport_ImportModule(PCRE2_CAPI_MODULE_NAME);
    if (pcre2_module == nullptr) {
        return -1;
    }
    const Pcre2Capi *capi = (const Pcre2Capi *)PyCapsule_Import(PCRE2_CAPI_CAPSULE_NAME, 0);
    Py_DECREF(pcre2_module);
    if (capi == nullptr) {
        return -1;
    }

    // abi_version and struct_size lead the struct in every version of it, so are always safe to read.
    if (capi->abi_version != PCRE2_CAPI_ABI_VERSION || capi->struct_size < sizeof(Pcre2Capi)) {
        PyErr_Format(
            PyExc_ImportError,
            "incompatible %s: abi version %u with size %u, need version %u with size of at least %zu",
            PCRE2_CAPI_CAPSULE_NAME,
            capi->abi_version,
            capi->struct_size,
            PCRE2_CAPI_ABI_VERSION,
            sizeof(Pcre2Capi)
        );
        return -1;
    }
    state->capi = capi;

    state->probe_match_context = capi->match_context_create(nullptr);
    if (state->probe_match_context == nullptr) {
        PyErr_NoMemory();
        return -1;
    }
    capi->set_match_limit(state->probe_match_context, kProbeMatchLimit);

    state->TokenizerType = (PyTypeObject *)PyType_FromModuleAndSpec(module, &Tokenizer_spec, nullptr);
    if (state->TokenizerType == nullptr) {
        return -1;
    }
    if (PyModule_AddType(module, state->TokenizerType) < 0) {
        return -1;
    }

    if (PyModule_AddStringConstant(module, "GPT4_PATTERN", GPT4_PATTERN) < 0) {
        return -1;
    }

    return 0;
}

static int bpe_traverse(PyObject *module, visitproc visit, void *arg)
{
    bpe_state *state = get_bpe_state(module);
    Py_VISIT(state->TokenizerType);
    return 0;
}

static int bpe_clear(PyObject *module)
{
    bpe_state *state = get_bpe_state(module);
    Py_CLEAR(state->TokenizerType);
    return 0;
}

static void bpe_free(void *module)
{
    bpe_state *state = get_bpe_state((PyObject *)module);
    bpe_clear((PyObject *)module);
    if (state->probe_match_context != nullptr) {
        state->capi->match_context_free(state->probe_match_context);
        state->probe_match_context = nullptr;
    }
}

static struct PyModuleDef_Slot bpe_slots[] = {
    {Py_mod_exec, (void *)bpe_exec},
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {0, nullptr}
};

static struct PyModuleDef bpe_module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = _MODULE_NAME,
    .m_doc = bpe_doc,
    .m_size = sizeof(bpe_state),
    .m_slots = bpe_slots,
    .m_traverse = bpe_traverse,
    .m_clear = bpe_clear,
    .m_free = bpe_free,
};

extern "C" {

PyMODINIT_FUNC PyInit__bpe(void)
{
    return PyModuleDef_Init(&bpe_module);
}

}
