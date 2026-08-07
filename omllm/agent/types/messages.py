from omcore import marshal as msh

from ... import llm


##


type Message = llm.Message


##


@msh.register_global_lazy_init
def _install_standard_marshaling(cfgs: msh.ConfigRegistry) -> None:
    llm_message_subtypes = msh.polymorphism_from_subclasses(llm.Message).subtypes

    msh.install_standard_factories(
        cfgs,
        *msh.standard_polymorphism_factories(
            msh.Polymorphism(
                Message,
                llm_message_subtypes,
            ),
            msh.WrapperTypeTagging(),
        ),
    )
