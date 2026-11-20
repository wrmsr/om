from omcore.text.styled.grid.controls import show_controls


##


def display_job_text(text: str) -> str:
    return '\n'.join(show_controls(line.expandtabs()).text for line in text.split('\n'))
