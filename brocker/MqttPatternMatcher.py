import re

class MqttPatternMatcher:
    """
    A model to detect if a given MQTT topic matches or conflicts with existing 
    topic patterns, supporting single-level (+) and multi-level (#) wildcards.
    """

    def _pattern_to_regex(self, pattern: str) -> str:
        """
        Converts an MQTT topic pattern with wildcards into a regular expression.

        Args:
            pattern (str): The MQTT pattern (e.g., 'sensors/+/temp' or 'logs/#').

        Returns:
            str: A regular expression string for matching.
        """
        # Replace single-level wildcard '+' with a regex part that matches any characters
        # except the topic level separator '/'.
        regex = pattern.replace('+', '[^/]+')

        # Handle the multi-level wildcard '#'.
        if regex.endswith('/#'):
            # If pattern is 'some/topic/#', it should match 'some/topic' and 'some/topic/...'
            # The '(?:/.*)?' part makes the slash and subsequent levels optional.
            regex = regex[:-2] + '(?:/.*)?'
        elif regex == '#':
            # If the pattern is just '#', it matches everything.
            regex = '.*'
        
        # Anchor the regex to match the entire topic string.
        return f"^{regex}$"

    def is_match(self, topic: str, pattern_list: list[str]) -> dict:
        """
        Checks if the topic matches or overlaps with any pattern in the provided list.

        Input:
            topic (string): The MQTT topic to check.
            pattern_list (list of strings): Existing topic patterns that may include wildcards.

        Output:
            match (boolean): True if the topic matches or overlaps with any existing 
                             pattern, False otherwise.
        """
        for pattern in pattern_list:
            regex_pattern = self._pattern_to_regex(pattern)
            if re.match(regex_pattern, topic):
                # If a match is found with any pattern, return immediately.
                return {"match": True}
        
        # If no patterns matched after checking the whole list.
        return {"match": False}

# --- Example Usage ---
if __name__ == "__main__":
    # Define a list of existing topic patterns (Training Data / Rules)
    existing_patterns = [
        "sensors/+/temperature",
        "alerts/critical/#",
        "devices/+/status",
        "system/logs"
    ]

    matcher = MqttPatternMatcher()

    print("--- Use Cases ---")

    # 1. Topic that matches a single-level wildcard pattern
    topic1 = "sensors/living_room/temperature"
    result1 = matcher.is_match(topic1, existing_patterns)
    print(f"Topic: '{topic1}'\nResult: {result1}\n") # Expected: {'match': True}

    # 2. Topic that matches a multi-level wildcard pattern
    topic2 = "alerts/critical/database/high_latency"
    result2 = matcher.is_match(topic2, existing_patterns)
    print(f"Topic: '{topic2}'\nResult: {result2}\n") # Expected: {'match': True}

    # 3. Topic that does NOT match any pattern
    topic3 = "sensors/living_room/humidity"
    result3 = matcher.is_match(topic3, existing_patterns)
    print(f"Topic: '{topic3}'\nResult: {result3}\n") # Expected: {'match': False}
    
    # 4. An exact match with a non-wildcard pattern
    topic4 = "system/logs"
    result4 = matcher.is_match(topic4, existing_patterns)
    print(f"Topic: '{topic4}'\nResult: {result4}\n") # Expected: {'match': True}
    
    # 5. Edge case: A topic that matches the parent level of a multi-level wildcard
    # The pattern 'alerts/critical/#' should match 'alerts/critical'
    topic5 = "alerts/critical"
    result5 = matcher.is_match(topic5, existing_patterns)
    print(f"Topic: '{topic5}'\nResult: {result5}\n") # Expected: {'match': True}
    
    # 6. Topic that is a level deeper than a single-level wildcard allows
    topic6 = "devices/bedroom/light/status"
    result6 = matcher.is_match(topic6, existing_patterns)
    print(f"Topic: '{topic6}'\nResult: {result6}\n") # Expected: {'match': False}