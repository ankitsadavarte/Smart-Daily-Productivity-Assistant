"""
Agent Development Kit (ADK) Integration Example.
Demonstrates how to use the enhanced tool capabilities in your Smart Daily Productivity Assistant.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import OrchestratorAgent
from tools.tool_registry import get_tool_registry
from tools.base_tool import ToolInput
from config.settings import get_config
import json

def demo_adk_integration():
    """Demonstrate Agent Development Kit integration."""
    print("🛠️ Agent Development Kit (ADK) Integration Demo")
    print("=" * 50)
    
    # Initialize orchestrator with ADK tools
    config = get_config()
    orchestrator = OrchestratorAgent(config['api_keys'])
    
    print("🔧 ADK Tools Available:")
    tool_registry = get_tool_registry()
    available_tools = tool_registry.list_tools()
    for tool_name in available_tools:
        tool = tool_registry.get_tool(tool_name)
        description = tool.description if tool else "Tool not found"
        print(f"   • {tool_name}: {description}")
    print()
    
    return orchestrator, tool_registry

def demo_weather_tool(tool_registry):
    """Demonstrate weather tool capabilities."""
    print("🌤️ Weather Tool Demo")
    print("-" * 30)
    
    weather_tool = tool_registry.get_tool('weather_service')
    if weather_tool:
        # Get current weather
        input_data = ToolInput(
            query="current weather",
            parameters={'location': 'New York'}
        )
        
        result = weather_tool.execute(input_data)
        print(f"Weather Query Result:")
        print(f"Success: {result.success}")
        if result.success:
            weather_data = result.result.get('weather', {})
            recommendations = result.result.get('scheduling_recommendations', [])
            print(f"Location: {weather_data.get('location', 'N/A')}")
            print(f"Temperature: {weather_data.get('temperature', 'N/A')}°F")
            print(f"Condition: {weather_data.get('condition', 'N/A')}")
            print(f"Scheduling Recommendations:")
            for rec in recommendations[:2]:
                print(f"   • {rec}")
        print()

def demo_search_tool(tool_registry):
    """Demonstrate search tool capabilities."""
    print("🔍 Search Tool Demo")
    print("-" * 30)
    
    search_tool = tool_registry.get_tool('google_search')
    if search_tool:
        # Search for productivity information
        input_data = ToolInput(
            query="best time of day for creative work productivity",
            parameters={'num_results': 3}
        )
        
        result = search_tool.execute(input_data)
        print(f"Search Query Result:")
        print(f"Success: {result.success}")
        if result.success and result.result:
            print("Search Results:")
            for i, item in enumerate(result.result[:2], 1):
                print(f"   {i}. {item.get('title', 'N/A')}")
                print(f"      {item.get('snippet', 'N/A')[:100]}...")
                print(f"      Source: {item.get('displayLink', 'N/A')}")
        print()

def demo_calendar_tool(tool_registry):
    """Demonstrate calendar tool capabilities."""
    print("📅 Calendar Tool Demo")
    print("-" * 30)
    
    calendar_tool = tool_registry.get_tool('calendar_manager')
    if calendar_tool:
        # Add a test event
        input_data = ToolInput(
            query="add event",
            parameters={
                'title': 'Team Meeting',
                'start': '2025-11-28T14:00:00',
                'end': '2025-11-28T15:00:00',
                'description': 'Weekly team sync meeting'
            }
        )
        
        result = calendar_tool.execute(input_data)
        print(f"Add Event Result:")
        print(f"Success: {result.success}")
        if result.success:
            print(f"Event Created: {result.result.get('title', 'N/A')}")
            print(f"Event ID: {result.result.get('id', 'N/A')}")
        
        # Check availability
        input_data = ToolInput(
            query="check availability",
            parameters={
                'start_time': '2025-11-28T13:00:00',
                'end_time': '2025-11-28T16:00:00'
            }
        )
        
        result = calendar_tool.execute(input_data)
        print(f"\\nAvailability Check:")
        print(f"Success: {result.success}")
        if result.success:
            availability_data = result.result
            print(f"Is Available: {availability_data.get('is_available', 'N/A')}")
            print(f"Conflicts Found: {len(availability_data.get('conflicts', []))}")
            print(f"Available Slots: {len(availability_data.get('available_slots', []))}")
        print()

def demo_enhanced_knowledge_agent(orchestrator):
    """Demonstrate enhanced knowledge agent with ADK tools."""
    print("🧠 Enhanced Knowledge Agent Demo")
    print("-" * 30)
    
    # Test weather-aware insights
    print("Testing weather-aware insights:")
    response = orchestrator.knowledge_agent.fetch_insights_with_tools(
        ["weather forecast for outdoor activities"], 
        location="New York"
    )
    insights = json.loads(response)
    for insight in insights:
        print(f"   • Query: {insight.get('query', 'N/A')}")
        print(f"   • Summary: {insight.get('summary', 'N/A')}")
        print(f"   • Source: {insight.get('source', 'N/A')}")
        print(f"   • Schedule Impact: {insight.get('suggested_schedule_impact', 'None')}")
    print()
    
    # Test search-powered insights
    print("Testing search-powered insights:")
    response = orchestrator.knowledge_agent.fetch_insights_with_tools(
        ["research productivity timing for analytical work"]
    )
    insights = json.loads(response)
    for insight in insights:
        print(f"   • Query: {insight.get('query', 'N/A')}")
        print(f"   • Summary: {insight.get('summary', 'N/A')}")
        print(f"   • Source: {insight.get('source', 'N/A')}")
    print()

def demo_tool_usage_statistics(tool_registry):
    """Demonstrate tool usage analytics."""
    print("📊 Tool Usage Statistics")
    print("-" * 30)
    
    stats = tool_registry.get_usage_statistics()
    for tool_name, tool_stats in stats.items():
        print(f"   • {tool_name}:")
        print(f"     Usage Count: {tool_stats.get('usage_count', 0)}")
        print(f"     Last Used: {tool_stats.get('last_used', 'Never')}")
    print()

def main():
    """Run ADK integration demonstration."""
    print("🚀 Smart Daily Productivity Assistant")
    print("🛠️ Agent Development Kit (ADK) Integration")
    print("=" * 60)
    print("This demo shows enhanced capabilities with ADK tools integration.\\n")
    
    try:
        # Initialize system with ADK
        orchestrator, tool_registry = demo_adk_integration()
        
        # Demonstrate individual tools
        demo_weather_tool(tool_registry)
        demo_search_tool(tool_registry)
        demo_calendar_tool(tool_registry)
        
        # Demonstrate enhanced agent capabilities
        demo_enhanced_knowledge_agent(orchestrator)
        
        # Show usage analytics
        demo_tool_usage_statistics(tool_registry)
        
        print("✅ ADK Integration Demo Completed Successfully!")
        print("\\n💡 Key ADK Benefits:")
        print("   • Standardized tool interface for all agents")
        print("   • Enhanced Google Search integration with your API key") 
        print("   • Advanced weather insights for context-aware scheduling")
        print("   • Calendar management with conflict detection")
        print("   • Usage analytics and tool monitoring")
        print("   • Extensible architecture for adding new tools")
        
    except Exception as e:
        print(f"❌ Error during ADK demo: {e}")

if __name__ == "__main__":
    main()