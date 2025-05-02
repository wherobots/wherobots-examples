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
                    cell.source = ""
        return cell, resources

# Export all the notebooks in the current directory to the sphinx_howto format
c = get_config()
c.NbConvertApp.notebooks = ["*.ipynb"]
c.Exporter.filters = {"comment_magics": comment_magics}

# Add the custom preprocessor to remove cells containing either "SedonaKepler", "create_map", or "add_df"
c.Exporter.preprocessors = [
    (RemoveCodeCellsWithContent(["SedonaKepler", "create_map", "add_df", "kepler_map", "map_config.json"]))
]
