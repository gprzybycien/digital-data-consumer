"""Reversible native chat-choice pilot. No connections, data queries or mutations."""
from typing import Dict
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from ibm_watsonx_orchestrate.run.widgets.forms import FormWidget, RadioButton, ToolEvent, MessageEvent
from ibm_watsonx_orchestrate.run.tool_result import ToolResult, TextContent, Annotations, Role

AREAS = ['Engagement', 'Conversion performance', 'Budget planning', 'Customer consent']
QUESTIONS = {
    'engagement': [
        'How many recorded clicks and impressions did each campaign generate?',
        'Which marketing channels have the most recorded clicks and impressions?',
        'How do recorded clicks and impressions change over time for a campaign?'],
    'conversion performance': [
        'How many bookings and paid bookings does each campaign have?',
        'How do daily booking counts and paid amounts compare by conversion cohort?',
        'How much recorded paid-booking amount is associated with each campaign?'],
    'budget planning': [
        'What is the planned budget for each campaign?',
        'Which campaigns have the largest planned budgets?',
        'What are the planned budgets and scheduled dates by marketing channel?'],
    'customer consent': [
        'How many distinct converters currently have recorded marketing opt-in?',
        'How does current opt-in among converters vary by campaign?',
        'What does the current opt-in measure mean and what are its limitations?']}
ACTIONS = ['Explain the selected question and measures', 'Show semantic verification for the selected question', 'Check readiness for the selected question']
ALLOWED = set(AREAS + ACTIONS + [q for rows in QUESTIONS.values() for q in rows])

@tool(permission=ToolPermission.READ_ONLY)
def show_consumer_next_steps(area: str = '', stage: str = 'questions') -> ToolResult:
    """Show clickable next choices: areas initially, business questions after area selection, actions after question selection. Metadata only; never queries or subscribes."""
    if stage == 'areas':
        choices = AREAS
    elif stage == 'questions' and area.casefold().strip() in QUESTIONS:
        choices = QUESTIONS[area.casefold().strip()]
    elif stage == 'actions':
        choices = ACTIONS
    else:
        raise ValueError('Choose a known navigation area and stage areas/questions/actions.')
    form = FormWidget(name='consumer_next_steps', title='What would you like to explore?',
        description='Select an option, then Continue. This refines your question; it does not run a query or create a subscription.',
        inputs=[RadioButton(name='choice', title='Next step', required=True, options=choices, option_labels=choices)],
        submit_text='Continue', cancel_text='Keep chatting',
        on_event=[ToolEvent(tool='select_consumer_next_step', parameters={'choice': ''}, map_input_to='submit'),
                  MessageEvent(message='Continue from my selected next step returned by select_consumer_next_step. Help me understand or refine it, metadata only. Do not calculate results or create a subscription.')])
    return ToolResult(content=[TextContent(text='Choose a next step below, or type your own question.', annotations=Annotations(audience=[Role.USER]))], widget=form)

@tool(permission=ToolPermission.READ_ONLY)
def select_consumer_next_step(choice: str) -> Dict:
    """Validate a submitted discovery choice and return it to the conversation. Selection is metadata-only and does not authorize SQL or subscription creation."""
    if choice not in ALLOWED:
        raise ValueError('Unknown discovery choice; use the displayed options or type a new question.')
    return {'success': True, 'selected_next_step': choice, 'intent': 'understand_or_refine',
            'sql_authorized': False, 'subscription_authorized': False,
            'next_stage': 'questions' if choice in AREAS else 'actions',
            'instruction': 'Advance within the selected area; retain context and resolve only missing period, grouping or time basis. Do not repeat the domain area menu.'}
