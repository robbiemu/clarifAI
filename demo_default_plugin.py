"""
Integration example showing how to use the default plugin with the orchestrator.

This demonstrates the basic usage of the plugin system and default plugin
for processing unstructured conversation data.
"""

import sys
import tempfile
from pathlib import Path

# Add the shared module to the path
sys.path.append(str(Path(__file__).parent / "shared"))

# Import the plugin system
from clarifai_shared import DefaultPlugin, convert_file_to_markdowns


def demo_default_plugin():
    """Demonstrate the default plugin functionality."""
    print("=== ClarifAI Default Plugin Demo ===\n")
    
    # Create some sample conversation data
    sample_data = """
CONVERSATION_LOG_v1.0
====================
SESSION_ID: demo_001
TOPIC: Sprint Planning
PARTICIPANTS: alice, bob, charlie

ENTRY [09:00:00] alice >> Let's start our sprint planning meeting.
ENTRY [09:00:15] bob >> I've prepared the backlog for review.
ENTRY [09:00:30] charlie >> Great! I see we have 15 user stories to estimate.
ENTRY [09:01:00] alice >> Let's start with the authentication improvements.
ENTRY [09:01:20] bob >> That should be a 3-point story based on complexity.
ENTRY [09:01:45] charlie >> I agree. It touches multiple components but the scope is clear.

SESSION_END: 09:05:00
DURATION: 5m0s
    """
    
    # Create a temporary file with the sample data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(sample_data)
        temp_path = Path(f.name)
    
    try:
        print("Sample input data:")
        print(sample_data)
        print("\n" + "="*50 + "\n")
        
        # Create plugin registry with the default plugin
        default_plugin = DefaultPlugin()
        registry = [default_plugin]
        
        print("Processing with DefaultPlugin...")
        
        # Convert the file
        outputs = convert_file_to_markdowns(temp_path, registry)
        
        print(f"✅ Successfully processed file!")
        print(f"📊 Extracted {len(outputs)} conversation(s)")
        
        if outputs:
            output = outputs[0]
            print(f"\n📝 Conversation Details:")
            print(f"   Title: {output.title}")
            print(f"   Participants: {output.metadata['participants']}")
            print(f"   Message Count: {output.metadata['message_count']}")
            print(f"   Plugin Used: {output.metadata['plugin_metadata']['source_format']}")
            
            print(f"\n📄 Generated Markdown (first 800 chars):")
            print("-" * 40)
            print(output.markdown_text[:800])
            if len(output.markdown_text) > 800:
                print("...")
            print("-" * 40)
        
    finally:
        # Clean up
        temp_path.unlink()


def demo_plugin_orchestrator():
    """Demonstrate plugin orchestrator behavior."""
    print("\n=== Plugin Orchestrator Demo ===\n")
    
    # Test with simple speaker:message format
    simple_conversation = """
john: Hey, how's the project going?
jane: Pretty well! We're ahead of schedule.
john: That's great news. Any blockers?
jane: Just waiting on the design review.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(simple_conversation)
        temp_path = Path(f.name)
    
    try:
        print("Testing with simple conversation format:")
        print(simple_conversation)
        
        # In a real system, this would try other plugins first
        # For now, we just demonstrate the default plugin
        registry = [DefaultPlugin()]
        
        outputs = convert_file_to_markdowns(temp_path, registry)
        
        if outputs:
            print(f"✅ DefaultPlugin successfully processed the file")
            print(f"📊 Extracted conversation with {len(outputs[0].metadata['participants'])} participants")
        else:
            print("❌ No conversation detected")
            
    finally:
        temp_path.unlink()


def demo_plugin_interface():
    """Demonstrate the plugin interface."""
    print("\n=== Plugin Interface Demo ===\n")
    
    # Show how the default plugin always accepts input
    plugin = DefaultPlugin()
    
    test_inputs = [
        "random text with no conversation",
        "alice: hello\nbob: hi there",
        "ENTRY [10:00] speaker >> message",
        "",
        "1234567890 !@#$%^&*()"
    ]
    
    print("Testing can_accept() method:")
    for i, test_input in enumerate(test_inputs, 1):
        accepts = plugin.can_accept(test_input)
        print(f"  {i}. '{test_input[:30]}{'...' if len(test_input) > 30 else ''}' -> {accepts}")
    
    print(f"\n✅ DefaultPlugin always returns True (fallback behavior)")


if __name__ == "__main__":
    demo_default_plugin()
    demo_plugin_orchestrator()
    demo_plugin_interface()
    
    print("\n🎉 Demo completed! The default plugin is ready for integration.")
    print("\nNext steps:")
    print("- Integrate with the orchestrator system (Sprint 8)")
    print("- Add more specific format plugins")
    print("- Configure LLM credentials for enhanced conversation extraction")