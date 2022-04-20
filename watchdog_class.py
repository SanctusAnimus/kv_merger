from watchdog.events import PatternMatchingEventHandler
from time import time
from merger import merge_profile


class FsChangesHandler(PatternMatchingEventHandler):
    def __init__(self):
        super().__init__(patterns=["*.txt", "*.kv"], ignore_directories=True)
        self.observed_profiles = []
        self.debounce_time = time()

    def on_any_event(self, event):
        # not interested in created events since we use watchdog to gather content
        # and created files don't have any content by default
        if event.event_type == "created":
            return
        # some actions (and some IDEs) cause multiple events to fire within a small time gap
        # discard such occurrences
        trigger_time = time()
        if trigger_time - self.debounce_time < 0.2:
            # print("debounced", trigger_time - self.debounce_time, event)
            return
        self.debounce_time = trigger_time
        # print(event.event_type, event.src_path[2:], event)
        for profile in self.observed_profiles:
            if not profile["source_dir"] or not profile["target_file_name"]:
                continue
            if event.src_path[2:].startswith(profile["source_dir"]):
                # print("detected change in observed profile", profile["name"])
                merge_profile(profile)

    def update_profiles(self, profiles: list[dict]):
        self.observed_profiles = profiles
