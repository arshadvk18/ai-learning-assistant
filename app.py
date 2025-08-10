# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

class LearningPathGenerator:
    def __init__(self):
        self.model = model
    
    def generate_learning_path(self, topic, level, timeframe, goals=""):
        """Generate a structured learning path using Gemini API"""
        
        prompt = f"""
        Create a detailed learning path for "{topic}" with the following requirements:
        - Current Level: {level}
        - Timeframe: {timeframe}
        - Specific Goals: {goals if goals else "General mastery"}
        
        Please provide a JSON response with this exact structure:
        {{
            "title": "Learning path title",
            "description": "Brief description of the learning journey",
            "steps": [
                {{
                    "title": "Step name",
                    "description": "Detailed description of what to learn and do",
                    "duration": "Time estimate (e.g., '3-4 days and also each day hours')",
                    "resources": ["list", "of", "recommended", "resources"],
                    "key_concepts": ["concept1", "concept2", "concept3"],
                    "practical_tasks": ["task1", "task2"]
                }}
            ],
            "total_estimated_time": "Total hours estimate",
            "difficulty_progression": "beginner to intermediate/advanced",
            "success_metrics": ["How to measure progress"]
        }}
        
        Make the path practical, actionable, and appropriate for the {level} level.
        Include 4-6 steps that progressively build knowledge.
        Focus on hands-on learning and real projects.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            text = response.text.strip()
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Fallback if no JSON found
                return self._create_fallback_path(topic, level, timeframe)
                
        except Exception as e:
            print(f"Error generating learning path: {e}")
            return self._create_fallback_path(topic, level, timeframe)
    
    def generate_quiz(self, topic, level, num_questions=5):
        """Generate a quiz based on the topic and level"""
        
        prompt = f"""
        Create a quiz about "{topic}" for {level} level with {num_questions} questions.
        
        Please provide a JSON response with this exact structure:
        {{
            "questions": [
                {{
                    "question": "Question text here?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": 0,
                    "explanation": "Why this answer is correct"
                }}
            ]
        }}
        
        Make questions practical and test real understanding, not just memorization.
        Include questions about concepts, best practices, and practical applications.
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                quiz_data = json.loads(json_str)
                return quiz_data.get('questions', [])
            else:
                return self._create_fallback_quiz(topic, level)
                
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return self._create_fallback_quiz(topic, level)
    
    def _create_fallback_path(self, topic, level, timeframe):
        """Fallback learning path if API fails"""
        return {
            "title": f"{topic} Learning Path",
            "description": f"A structured {level}-level approach to learning {topic}",
            "steps": [
                {
                    "title": "Foundation & Setup",
                    "description": f"Get started with {topic} fundamentals and environment setup",
                    "duration": "2-3 days",
                    "resources": ["Official documentation", "Setup guides", "Beginner tutorials"],
                    "key_concepts": ["Basic terminology", "Environment setup", "First steps"],
                    "practical_tasks": ["Install tools", "Run hello world", "Basic exercises"]
                },
                {
                    "title": "Core Concepts",
                    "description": f"Master the fundamental concepts and principles of {topic}",
                    "duration": "1 week",
                    "resources": ["Interactive tutorials", "Documentation", "Practice exercises"],
                    "key_concepts": ["Core principles", "Best practices", "Common patterns"],
                    "practical_tasks": ["Build simple projects", "Complete exercises", "Code reviews"]
                },
                {
                    "title": "Practical Application",
                    "description": f"Apply {topic} knowledge through real-world projects",
                    "duration": "1-2 weeks",
                    "resources": ["Project ideas", "GitHub repos", "Community forums"],
                    "key_concepts": ["Project structure", "Real-world patterns", "Problem solving"],
                    "practical_tasks": ["Build portfolio project", "Deploy application", "Get feedback"]
                }
            ],
            "total_estimated_time": "40-60 hours",
            "difficulty_progression": f"{level} to intermediate",
            "success_metrics": ["Completed projects", "Understanding of concepts", "Ability to solve problems"]
        }
    
    def _create_fallback_quiz(self, topic, level):
        """Fallback quiz if API fails"""
        return [
            {
                "question": f"What is the most important first step when learning {topic}?",
                "options": [
                    "Jump into advanced topics immediately",
                    "Understand fundamentals and set up environment",
                    "Memorize syntax without practice",
                    "Skip documentation completely"
                ],
                "correct_answer": 1,
                "explanation": "Starting with fundamentals and proper setup creates a strong foundation"
            },
            {
                "question": f"Which is the best approach for mastering {topic}?",
                "options": [
                    "Only read theory",
                    "Only watch videos",
                    "Combine theory with hands-on practice",
                    "Copy code without understanding"
                ],
                "correct_answer": 2,
                "explanation": "Combining theory with practice reinforces learning and builds practical skills"
            }
        ]

# Initialize the learning path generator
generator = LearningPathGenerator()

@app.route('/api/generate-learning-path', methods=['POST'])
def generate_learning_path():
    """API endpoint to generate learning path"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'topic' not in data:
            return jsonify({'error': 'Topic is required'}), 400
        
        topic = data['topic']
        level = data.get('level', 'beginner')
        timeframe = data.get('timeframe', '1 month')
        goals = data.get('goals', '')
        
        # Generate learning path
        learning_path = generator.generate_learning_path(topic, level, timeframe, goals)
        
        # Generate quiz
        quiz_questions = generator.generate_quiz(topic, level)
        
        # Calculate stats
        total_steps = len(learning_path.get('steps', []))
        estimated_time = learning_path.get('total_estimated_time', '40-60 hours')
        
        # Extract numeric time estimate
        time_numbers = re.findall(r'\d+', estimated_time)
        avg_time = sum(int(x) for x in time_numbers) // len(time_numbers) if time_numbers else 50
        
        response_data = {
            'success': True,
            'learning_path': learning_path,
            'quiz': quiz_questions,
            'stats': {
                'total_steps': total_steps,
                'estimated_time': avg_time,
                'topic': topic,
                'level': level
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in generate_learning_path: {e}")
        return jsonify({'error': 'Failed to generate learning path'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Learning Assistant API is running'})

@app.route('/api/quiz-feedback', methods=['POST'])
def quiz_feedback():
    """Provide detailed feedback on quiz answers"""
    try:
        data = request.get_json()
        topic = data.get('topic')
        user_answers = data.get('answers', [])
        correct_answers = data.get('correct_answers', [])
        
        # Generate personalized feedback using Gemini
        prompt = f"""
        Based on a {topic} quiz, provide personalized learning feedback.
        
        User got {sum(1 for i, ans in enumerate(user_answers) if ans == correct_answers[i])} out of {len(user_answers)} questions correct.
        
        Provide a JSON response with:
        {{
            "overall_feedback": "General assessment and encouragement",
            "strengths": ["areas where user performed well"],
            "improvement_areas": ["concepts to focus on"],
            "next_steps": ["specific recommendations for learning"],
            "resources": ["recommended resources for improvement"]
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            
            if json_match:
                feedback_data = json.loads(json_match.group())
            else:
                feedback_data = {
                    "overall_feedback": "Keep practicing to improve your understanding!",
                    "strengths": ["Attempted all questions"],
                    "improvement_areas": ["Review core concepts"],
                    "next_steps": ["Practice more exercises", "Review documentation"],
                    "resources": ["Official tutorials", "Practice platforms"]
                }
        except:
            feedback_data = {
                "overall_feedback": "Keep practicing to improve your understanding!",
                "strengths": ["Attempted all questions"],
                "improvement_areas": ["Review core concepts"],
                "next_steps": ["Practice more exercises"],
                "resources": ["Official tutorials"]
            }
        
        return jsonify({'success': True, 'feedback': feedback_data})
        
    except Exception as e:
        print(f"Error generating feedback: {e}")
        return jsonify({'error': 'Failed to generate feedback'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)