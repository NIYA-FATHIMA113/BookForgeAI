from tenants.models import Tenant


QUESTION_VARIANTS = {
    "business_name": [
        "Tell me a little about your business. What is it called, what kind of business is it, and where is it based?",
        "Let's get the basics right first: what name should appear on the website, what do you do, and which city are you in?",
        "What should customers call your business, what type is it, and where can they find you?",
    ],
    "business_type": [
        "What kind of business is {name}? You can also tell me which city it's in.",
        "How would you describe {name} to a new customer, and where is it based?",
        "What type of business should I set up for {name}? A location is helpful too.",
    ],
    "services": {
        "restaurant": [
            "What food or menu items would you like guests to see? You can mention your cuisine or signature dishes.",
            "Tell me about your menu at {name}. What do you serve, and are there any specialties to highlight?",
            "What can guests enjoy at {name}? Share menu items or cuisine details you want on the site.",
        ],
        "salon": [
            "What treatments or services can customers book? Add prices or durations if you know them.",
            "Tell me what customers can book at {name}, with any prices and durations you have.",
            "Which salon services should appear on your website? Prices and appointment lengths are optional.",
        ],
        "clinic": [
            "Which consultations or treatments can patients book? You can include prices or appointment lengths.",
            "What appointment types should patients see for {name}? Add prices or durations if available.",
            "Tell me which consultations you provide. I’ll only add the services you specify.",
        ],
        "sports_turf": [
            "What activities or booking options do you offer, such as pitch sizes or match types?",
            "What can customers reserve at {name}? Include activity names and durations or prices if known.",
            "Which sports or facilities should customers be able to book? I won't add anything you don't mention.",
        ],
        "default": [
            "What services or activities should customers be able to book? Prices and durations are optional.",
            "Tell me what customers can book with {name}. I'll list only the offerings you provide.",
            "Which offerings should appear on your website? Include prices or durations if you know them.",
        ],
    },
    "opening_time": [
        "What days and hours are you open? A simple answer like ‘Tuesday to Sunday, 10 AM to 8 PM’ works.",
        "Could you share your weekly schedule, including opening and closing times?",
        "When can customers visit or book? Tell me the days you operate and the hours.",
    ],
    "closing_time": [
        "What time do you close, and what days are you open? Please include AM or PM if needed.",
        "Could you share your opening and closing times along with your operating days?",
        "What is your weekly schedule? For example, open daily from 10 AM to 8 PM.",
    ],
    "working_days": [
        "Which days do you operate, and what are your opening and closing times?",
        "Are you open every day or do you have regular closing days? Please include your hours.",
        "What days can customers visit? You can give the full weekly schedule in one message.",
    ],
    "number_of_resources": {
        "restaurant": [
            "How many tables can guests reserve? If you have separate dining areas, you can mention those too.",
            "How many reservable tables should the booking system make available?",
            "How many tables can you seat at the same time?",
        ],
        "salon": [
            "How many styling chairs or treatment rooms can serve customers at the same time?",
            "How many customers can you accommodate at once, across chairs or treatment rooms?",
            "How many bookable chairs or rooms should I set up?",
        ],
        "clinic": [
            "How many consultation rooms or appointment slots can you accommodate at once?",
            "How many patients can you see at the same time? You can describe rooms or slots.",
            "How many bookable rooms or appointment spaces should I set up?",
        ],
        "sports_turf": [
            "How many pitches or courts can customers book at the same time?",
            "How many bookable fields or sports spaces do you have?",
            "What booking capacity should I set up, such as the number of pitches?",
        ],
        "default": [
            "How many rooms, chairs, tables, staff slots, or other bookable spaces can you use at once?",
            "What booking capacity should the system account for? Describe only resources that apply.",
            "How many bookable spaces or concurrent appointments can you accommodate?",
        ],
    },
    "website_style": [
        "How should your website feel to a first-time visitor: modern, elegant, warm, natural, bold, or playful?",
        "What kind of look fits your business? You can name a style, or tell me to choose a suitable one.",
        "Would you like a modern, premium, welcoming, natural, energetic, or playful look? I can recommend one for your business too.",
    ],
    "contact_details": [
        "What phone number or email should customers see on the website? You can also skip this.",
        "How can customers contact {name}? Share a phone number, an email, or say ‘skip’ for now.",
        "Would you like to add a customer-facing phone number or email address?",
    ],
}


PLACEHOLDERS = {
    "business_name": "e.g. Restaurant name, type, and city",
    "business_type": "e.g. A family restaurant in Calicut",
    "services": {
        "restaurant": "e.g. Kerala cuisine, seafood, vegetarian dishes",
        "salon": "e.g. Haircut ₹450 (30 min), facial ₹900 (45 min)",
        "clinic": "e.g. General consultation ₹500 (20 min)",
        "sports_turf": "e.g. 5-a-side football, 7-a-side football",
        "default": "e.g. Service name, price, and appointment length",
    },
    "opening_time": "e.g. Open daily from 11 AM to 11 PM",
    "closing_time": "e.g. Tuesday to Sunday, 10 AM to 8 PM",
    "working_days": "e.g. Tuesday through Sunday, 10 AM to 8 PM",
    "number_of_resources": {
        "restaurant": "e.g. We have 20 dining tables",
        "salon": "e.g. 4 styling chairs and 2 treatment rooms",
        "clinic": "e.g. 3 consultation rooms",
        "sports_turf": "e.g. We have 2 football pitches",
        "default": "e.g. 4 bookable rooms or spaces",
    },
    "website_style": "e.g. Modern and elegant, or choose what suits my business",
    "contact_details": "e.g. Phone number or business email, or type skip",
}


def get_next_onboarding_topic(configuration, missing_fields):
    for topic in (
        "business_name", "business_type", "services", "opening_time",
        "closing_time", "working_days", "number_of_resources",
    ):
        if topic in missing_fields:
            return topic
    if not configuration.contact_details_reviewed:
        return "contact_details"
    if not configuration.website_style:
        return "website_style"
    return None


def get_onboarding_placeholder(topic, business_type=""):
    value = PLACEHOLDERS.get(topic, "Tell me a little more...")
    if isinstance(value, dict):
        return value.get(business_type, value["default"])
    return value


def get_onboarding_question(configuration, topic, variation=0):
    business_type = configuration.business_type or "default"
    variants = QUESTION_VARIANTS.get(topic)
    if isinstance(variants, dict):
        variants = variants.get(business_type, variants["default"])
    if not variants:
        return "What else should I know about your business?"
    question = variants[variation % len(variants)]
    name = configuration.business_name or "your business"
    return question.format(name=name)


def suggest_website_style(business_type):
    return {
        "restaurant": "warm",
        "salon": "elegant",
        "clinic": "modern",
        "sports_turf": "bold",
    }.get(business_type, "modern")


def get_setup_summary(configuration):
    lines = [
        f"- **Business:** {configuration.business_name}",
        f"- **Type:** {dict(Tenant.BUSINESS_TYPES).get(configuration.business_type, configuration.business_type)}",
    ]
    if configuration.location:
        lines.append(f"- **Location:** {configuration.location}")
    if configuration.services:
        lines.append("- **Offerings:** " + ", ".join(item["name"] for item in configuration.services))
    days = ", ".join(configuration.working_days or [])
    if configuration.opening_time and configuration.closing_time:
        hours = f"{configuration.opening_time.strftime('%I:%M %p').lstrip('0')}–{configuration.closing_time.strftime('%I:%M %p').lstrip('0')}"
        lines.append(f"- **Hours:** {days + ' · ' if days else ''}{hours}")
    if configuration.number_of_resources:
        lines.append(f"- **Capacity:** {configuration.number_of_resources} bookable spaces")
    if configuration.contact_phone:
        lines.append(f"- **Phone:** {configuration.contact_phone}")
    if configuration.contact_email:
        lines.append(f"- **Email:** {configuration.contact_email}")
    if configuration.website_style:
        source = "AI suggestion" if configuration.website_style_suggested else "your preference"
        lines.append(f"- **Website look ({source}):** {configuration.website_style.title()}")
    return "\n".join(lines)
