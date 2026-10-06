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

AREA_LABELS = [
    'Engagement — recorded clicks and impressions',
    'Conversion performance — bookings, paid bookings and amounts',
    'Budget planning — planned campaign budgets and schedules',
    'Customer consent — current opt-in among converters']
OVERVIEW = """**Explore Marketing analyses**

Start with the business question you want to answer:

- **Engagement:** compare recorded clicks and impressions by campaign or marketing channel, and examine trends over time.
- **Conversion performance:** compare bookings and paid bookings, recorded paid amounts, and daily conversion-cohort performance.
- **Budget planning:** review planned campaign budgets and schedules. Planned budgets do not represent actual advertising spend or ROI.
- **Customer consent:** understand current opt-in among converters. This does not establish historical consent or permission to contact someone.

These examples use the curated **Performance Marketing** product and business meanings in the **Marketing DPH** glossary. They are starting points, not the entire Marketing catalogue; current product support is checked when you select an analysis.

Choose an area below, or describe another question."""
AREA_CONTEXT = {
    'engagement': """**Engagement: understand campaign response**

Explore recorded clicks and impressions by campaign, marketing channel or event time. Relevant glossary meanings include **Recorded click count**, **Recorded impression count**, **Recorded campaign attribution** and **Marketing channel**.

The curated **Performance Marketing** product uses `digital_event` for interactions and `campaign` for campaign details. This is event activity, not unique audience reach or a complete impression-to-booking funnel; timestamp timezone still needs checking.

Choose a sample business question below, or write your own. The selected analysis will be checked against current product and glossary metadata.""",
    'conversion performance': """**Conversion performance: understand booking outcomes**

Compare bookings, paid bookings and recorded paid amounts, or explore daily conversion-cohort trends. Relevant glossary meanings include **Paid booking count**, **Payment completion timestamp** and **Paid booking amount by conversion cohort**.

The curated **Performance Marketing** product provides booking detail in `booking_conversion`, daily aggregates in `campaign_daily_performance`, and campaign context in `campaign`. A paid booking has recorded payment completion. Cohort amounts follow conversion date, not payment date; recorded amounts are not net accounting revenue.

Choose a sample question below. We will clarify the time basis and period before calculating anything.""",
    'budget planning': """**Budget planning: understand planned investment**

Review campaign budgets, schedules and marketing channels. The key glossary meaning is **Planned campaign budget**.

The curated **Performance Marketing** product provides these details in `campaign`. Budgets are planned allocations, not actual spend. ROI cannot be established from this data alone, and currency must be confirmed before comparing or adding amounts.

Choose a sample business question below, or write your own. Current product support will be checked for the selected analysis.""",
    'customer consent': """**Customer consent: understand current opt-in among converters**

Explore distinct converters with recorded current marketing opt-in. Relevant glossary meanings include **Marketing subject identifier**, **Recorded marketing opt-in state** and **Currently opted-in converter subjects per campaign day**.

The curated **Performance Marketing** product provides current consent in `customer_consent`, booking detail in `booking_conversion`, and daily aggregates in `campaign_daily_performance`. Current opt-in is not historical consent or permission for outreach; daily distinct counts cannot simply be added across days.

Choose a sample question below. Current assignments and product support will be checked for the selected analysis."""}

@tool(permission=ToolPermission.READ_ONLY)
def show_consumer_next_steps(area: str = '', stage: str = 'questions') -> ToolResult:
    """Show clickable next choices: areas initially, business questions after area selection, actions after question selection. Metadata only; never queries or subscribes."""
    if stage == 'areas':
        choices = AREAS
        labels = AREA_LABELS
        summary = OVERVIEW
        title = 'Choose a Marketing area'
    elif stage == 'questions' and area.casefold().strip() in QUESTIONS:
        choices = QUESTIONS[area.casefold().strip()]
        labels = choices
        summary = AREA_CONTEXT[area.casefold().strip()]
        title = 'Choose a business question'
    elif stage == 'actions':
        choices = ACTIONS
        labels = choices
        summary = 'You have selected a business question. We can explain its measures, inspect the semantic evidence, or check readiness to answer it. Any missing period, grouping or time basis should be clarified first.'
        title = 'Explore your selected question'
    else:
        raise ValueError('Choose a known navigation area and stage areas/questions/actions.')
    form = FormWidget(name='consumer_next_steps', title=title,
        description='Select an option and Continue, or keep chatting with your own question.',
        inputs=[RadioButton(name='choice', title='Next step', required=True, options=choices, option_labels=labels)],
        submit_text='Continue', cancel_text='Keep chatting',
        on_event=[ToolEvent(tool='select_consumer_next_step', parameters={'choice': ''}, map_input_to='submit'),
                  MessageEvent(message='Continue from my selected next step returned by select_consumer_next_step. Help me understand or refine it, metadata only. Do not calculate results or create a subscription.')])
    return ToolResult(content=[TextContent(text=summary, annotations=Annotations(audience=[Role.USER]))], widget=form)

@tool(permission=ToolPermission.READ_ONLY)
def select_consumer_next_step(choice: str) -> Dict:
    """Validate a submitted discovery choice and return it to the conversation. Selection is metadata-only and does not authorize SQL or subscription creation."""
    if choice not in ALLOWED:
        raise ValueError('Unknown discovery choice; use the displayed options or type a new question.')
    return {'success': True, 'selected_next_step': choice, 'intent': 'understand_or_refine',
            'sql_authorized': False, 'subscription_authorized': False,
            'next_stage': 'questions' if choice in AREAS else 'actions',
            'instruction': 'Advance within the selected area; retain context and resolve only missing period, grouping or time basis. Do not repeat the domain area menu.'}
