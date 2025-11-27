"""Main entry point for the agentic system."""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.workflow import AgenticWorkflow


def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python src/run.py \"Your query here\"")
        print("\nExample:")
        print('  python src/run.py "Analyze ROAS drop in last 7 days"')
        sys.exit(1)
    
    user_query = sys.argv[1]
    
    # Check for API key (if using LLM)
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not set. Using rule-based agents.")
        print("   Set OPENAI_API_KEY environment variable to use LLM-powered agents.\n")
    
    # Run workflow
    workflow = AgenticWorkflow()
    
    try:
        results = workflow.run(user_query)
        print("\n✨ Success! Check the reports/ directory for outputs.")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
