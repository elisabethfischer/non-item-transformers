from pathlib import Path
from asme.core.utils.ioutils import load_filtered_vocabulary

class FilterPredictionItems:
    """
    Load file with selected item ids for filtering results
    """

    def __init__(self, selected_items_file: Path, original_vocabulary_path: Path):
        self.selected_items = None
        if selected_items_file is not None:
            self.selected_items = load_filtered_vocabulary(selected_items_file,original_vocabulary_path)

    def get_selected_items(self):
        return self.selected_items






