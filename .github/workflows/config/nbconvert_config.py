from nbconvert.preprocessors import Preprocessor

def comment_magics(input, **kwargs):
    if input.startswith("%"):
        input = "# " + input
    return input

class RemoveCodeCellsWithContent(Preprocessor):
    def __init__(self, content_to_remove=None, **kw):
        super().__init__(**kw)
        self.content_to_remove = content_to_remove if content_to_remove is not None else []

    def preprocess_cell(self, cell, resources, cell_index):
        if cell.cell_type == 'code':
            for content in self.content_to_remove:
                if content in cell.source:
                    # comment out SedonaKepler import when SedonaContext is in the same cell
                    if "SedonaContext" in cell.source:
                        new_source_lines = []
                        for line in cell.source.splitlines():
                            if content in line:
                                new_source_lines.append("# " + line)
                            else:
                                new_source_lines.append(line)
                        cell.source = "\n".join(new_source_lines)
                        continue

                    cell.source = ""
                    break
            # comment out Jupyter magic command like "?"
            if "?" in cell.source:
                new_source_lines = []
                for line in cell.source.splitlines():
                    if "?" in line:
                        new_source_lines.append("# " + line)
                    else:
                        new_source_lines.append(line)
                cell.source = "\n".join(new_source_lines)
        return cell, resources

# Export all the notebooks in the current directory to the sphinx_howto format
c = get_config()
c.NbConvertApp.notebooks = ["*.ipynb"]
c.Exporter.filters = {"comment_magics": comment_magics}

# Add the custom preprocessor to remove cells containing either "SedonaKepler", "create_map", or "add_df"
c.Exporter.preprocessors = [
    (RemoveCodeCellsWithContent(["SedonaKepler", "create_map", "add_df", "kepler_map", "map_config.json", "SedonaPyDeck", "gdf.plot"]))
]
