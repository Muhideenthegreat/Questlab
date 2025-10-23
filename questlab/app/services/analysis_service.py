class AnalysisService:
    """Simple analysis service for submission feedback"""
    
    @staticmethod
    def analyze_submission(text, quest_tags=None):
        """Basic keyword analysis for feedback"""
        feedback_keywords = {
            'science': ['observe', 'experiment', 'hypothesis', 'data', 'results'],
            'physics': ['energy', 'motion', 'force', 'velocity', 'acceleration'],
            'biology': ['cell', 'organism', 'ecosystem', 'evolution', 'DNA'],
            'chemistry': ['element', 'compound', 'reaction', 'molecule', 'atom']
        }
        
        found_keywords = []
        text_lower = text.lower()
        
        if quest_tags:
            for tag in quest_tags:
                if tag in feedback_keywords:
                    for keyword in feedback_keywords[tag]:
                        if keyword in text_lower:
                            found_keywords.append(keyword)
        
        if found_keywords:
            return f"Great work! You used relevant concepts like: {', '.join(found_keywords[:3])}. Keep exploring!"
        else:
            return "Good reflection! Consider connecting your observations to specific scientific concepts in your next submission."