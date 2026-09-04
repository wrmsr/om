"""The default target-neutral theme for the semantic style names the styled renderer emits."""
from omcore.text import styled as st


##


# The textual-dark palette minitui ships as its default theme (see omdev.tui.minitui.text.themes for provenance). The
# values are copied here so the semantic UI names have one target-neutral definition that the terminal and html targets
# both layer over their own themes, while inline rendering stays free of omdev.
_TEXT_PRIMARY = st.parse_rgb('#57A5E2')
_TEXT_WARNING = st.parse_rgb('#FFC473')
_TEXT_ERROR = st.parse_rgb('#D17E92')
_WARNING = st.parse_rgb('#FEA62B')
_SUCCESS = st.parse_rgb('#71AC84')
_STRING_GREEN = st.parse_rgb('#8AD4A1')


UI_TEXT_STYLE_THEME = st.StyleTheme({
    'text.color.red': st.StylePatch(fg=_TEXT_ERROR),
    'text.color.green': st.StylePatch(fg=_SUCCESS),
    'text.color.yellow': st.StylePatch(fg=_WARNING),
    'text.color.blue': st.StylePatch(fg=_TEXT_PRIMARY),

    'json.key': st.StylePatch(fg=_TEXT_PRIMARY),
    'json.string': st.StylePatch(fg=_STRING_GREEN),
    'json.number': st.StylePatch(fg=_TEXT_WARNING),
    'json.literal': st.StylePatch(fg=_TEXT_PRIMARY),
})
