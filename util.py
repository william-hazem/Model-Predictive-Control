from IPython.display import display, Markdown

def print_matrix(name, M):
    """Exibe uma matriz formatada em Markdown no Google Colab."""
    M_str = "\n".join([" | ".join([f"{val:.4f}" for val in row]) for row in M])
    display(Markdown(f"**{name}:**\n\n```\n{M_str}\n```"))