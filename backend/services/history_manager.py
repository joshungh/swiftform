"""
History manager for storing and retrieving form generation history
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import uuid

class HistoryManager:
    def __init__(self, history_dir: str = "history"):
        self.history_dir = history_dir
        self.history_file = os.path.join(history_dir, "history.json")
        self.forms_dir = os.path.join(history_dir, "forms")

        # Create directories if they don't exist
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.forms_dir, exist_ok=True)

        # Initialize history file if it doesn't exist
        if not os.path.exists(self.history_file):
            self._save_history([])

    def _load_history(self) -> List[Dict]:
        """Load history from JSON file"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            return []

    def _save_history(self, history: List[Dict]):
        """Save history to JSON file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_to_history(self,
                       filename: str,
                       form_schema: Dict,
                       file_type: str,
                       processing_time: float = 0) -> str:
        """Add a new entry to history"""
        history = self._load_history()

        # Generate unique ID
        entry_id = str(uuid.uuid4())

        # Save form schema to separate file
        form_file = os.path.join(self.forms_dir, f"{entry_id}.json")
        with open(form_file, 'w') as f:
            json.dump(form_schema, f, indent=2)

        # Create history entry
        entry = {
            "id": entry_id,
            "filename": filename,
            "file_type": file_type,
            "created_at": datetime.now().isoformat(),
            "processing_time": processing_time,
            "form_file": form_file,
            "pages_count": len(form_schema.get("props", {}).get("children", [])),
            "fields_count": self._count_fields(form_schema)
        }

        # Add to beginning of list (most recent first)
        history.insert(0, entry)

        # Keep only last 100 entries
        if len(history) > 100:
            # Delete old form files
            for old_entry in history[100:]:
                old_form_file = old_entry.get("form_file")
                if old_form_file and os.path.exists(old_form_file):
                    try:
                        os.remove(old_form_file)
                    except:
                        pass

            history = history[:100]

        self._save_history(history)
        return entry_id

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get history entries"""
        history = self._load_history()
        return history[:limit]

    def get_entry(self, entry_id: str) -> Optional[Dict]:
        """Get a specific history entry with form schema"""
        history = self._load_history()

        for entry in history:
            if entry["id"] == entry_id:
                # Load form schema
                form_file = entry.get("form_file")
                if form_file and os.path.exists(form_file):
                    try:
                        with open(form_file, 'r') as f:
                            entry["form_schema"] = json.load(f)
                    except Exception as e:
                        print(f"Error loading form schema: {e}")
                        entry["form_schema"] = None

                return entry

        return None

    def delete_entry(self, entry_id: str) -> bool:
        """Delete a history entry"""
        history = self._load_history()

        for i, entry in enumerate(history):
            if entry["id"] == entry_id:
                # Delete form file
                form_file = entry.get("form_file")
                if form_file and os.path.exists(form_file):
                    try:
                        os.remove(form_file)
                    except:
                        pass

                # Remove from history
                history.pop(i)
                self._save_history(history)
                return True

        return False

    def clear_history(self) -> bool:
        """Clear all history"""
        try:
            # Delete all form files
            for file in os.listdir(self.forms_dir):
                file_path = os.path.join(self.forms_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)

            # Clear history
            self._save_history([])
            return True
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False

    def search_history(self, query: str) -> List[Dict]:
        """Search history by filename"""
        history = self._load_history()
        query_lower = query.lower()

        results = []
        for entry in history:
            if query_lower in entry.get("filename", "").lower():
                results.append(entry)

        return results

    def _count_fields(self, form_schema: Dict) -> int:
        """Count total fields in form schema"""
        count = 0
        for page in form_schema.get("props", {}).get("children", []):
            count += len(page.get("props", {}).get("children", []))
        return count