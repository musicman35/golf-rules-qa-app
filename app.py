"""
Golf Rules Q&A and Course Finder - Streamlit Application

A Python-friendly web application for golf rules questions and course search.
Uses Streamlit for the UI, Claude AI for intelligent responses, and RAG for accurate rules answers.
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger
import sys
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)
logger.add(sys.stderr, level="INFO")

# Import our modules
from rag.claude_qa import get_qa_system
from data.database import get_db
from data.updater import get_updater


# Page configuration
st.set_page_config(
    page_title="Golf Rules Q&A & Course Finder",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e7b34;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .freshness-indicator {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .freshness-green {
        background-color: #d4edda;
        color: #155724;
    }
    .freshness-yellow {
        background-color: #fff3cd;
        color: #856404;
    }
    .freshness-red {
        background-color: #f8d7da;
        color: #721c24;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #1e7b34;
    }
    .citation {
        background-color: #e9ecef;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.chat_history = []
        st.session_state.qa_system = None
        st.session_state.db = None
        st.session_state.updater = None


def initialize_app():
    """Initialize the application components."""
    if not st.session_state.initialized:
        with st.spinner("Initializing application..."):
            try:
                # Initialize components
                st.session_state.db = get_db()
                st.session_state.updater = get_updater()

                # Initialize data if needed (using sample data for quick start)
                st.session_state.updater.initialize_data(use_sample=True)

                # Initialize QA system
                st.session_state.qa_system = get_qa_system()

                st.session_state.initialized = True
                logger.info("Application initialized successfully")

            except Exception as e:
                st.error(f"Failed to initialize application: {str(e)}")
                logger.error(f"Initialization error: {e}")
                st.stop()


def display_data_freshness():
    """Display data freshness indicators in the sidebar."""
    st.sidebar.markdown("### 📊 Data Freshness")

    freshness = st.session_state.updater.get_data_freshness_status()

    for data_type, info in freshness.items():
        warning_level = info['warning_level']
        color_class = f"freshness-{warning_level}"

        # Format the display
        if info['age_days'] is not None:
            last_update = datetime.fromisoformat(info['last_update']).strftime('%Y-%m-%d')
            status_text = f"✓ {data_type.title()}: {info['age_days']} days ago ({last_update})"
        else:
            status_text = f"⚠ {data_type.title()}: Not initialized"

        st.sidebar.markdown(
            f'<div class="freshness-indicator {color_class}">{status_text}</div>',
            unsafe_allow_html=True
        )

    # Manual update button (for admins)
    if st.sidebar.button("🔄 Update Data Now"):
        with st.spinner("Updating data..."):
            result = st.session_state.updater.update_all(use_sample=True)
            if result['overall_success']:
                st.sidebar.success("Data updated successfully!")
                st.rerun()
            else:
                st.sidebar.error("Data update failed. Check logs.")


def rules_qa_page():
    """Rules Q&A page with chat interface."""
    st.markdown('<div class="main-header">⛳ USGA Rules Q&A</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask any question about the Rules of Golf</div>', unsafe_allow_html=True)

    # Example questions
    with st.expander("📚 Example Questions"):
        st.markdown("""
        - Can I repair a ball mark on the putting green?
        - What is the penalty for hitting a ball out of bounds?
        - Can I move loose impediments in a bunker?
        - What relief do I get from an embedded ball?
        - Can I ground my club in a penalty area?
        """)

    # Chat interface
    st.markdown("### 💬 Ask a Question")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show metadata for assistant messages
            if message["role"] == "assistant" and "metadata" in message:
                with st.expander("📋 Details"):
                    meta = message["metadata"]

                    # Show retrieved contexts
                    if "contexts" in meta and meta["contexts"]:
                        st.markdown("**Relevant Rules:**")
                        for i, ctx in enumerate(meta["contexts"][:3], 1):
                            rule_id = ctx['metadata'].get('rule_id', 'Unknown')
                            title = ctx['metadata'].get('title', '')
                            score = ctx.get('final_score', 0)
                            st.markdown(f"{i}. Rule {rule_id}: {title} (relevance: {score:.2f})")

                    # Show metrics
                    if "metrics" in meta:
                        metrics = meta["metrics"]
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Response Time", f"{metrics['response_time_ms']}ms")
                        col2.metric("Tokens Used", metrics['total_tokens'])
                        col3.metric("Cost", f"${metrics['cost_usd']:.4f}")

                    # Feedback buttons
                    if "query_id" in meta["metrics"]:
                        query_id = meta["metrics"]["query_id"]
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if st.button("👍", key=f"thumbs_up_{query_id}"):
                                st.session_state.db.update_query_feedback(query_id, 1)
                                st.success("Thanks for the feedback!")
                        with col2:
                            if st.button("👎", key=f"thumbs_down_{query_id}"):
                                st.session_state.db.update_query_feedback(query_id, -1)
                                st.success("Thanks for the feedback!")

    # Chat input
    if question := st.chat_input("Ask a golf rules question..."):
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": question})

        # Display user message
        with st.chat_message("user"):
            st.markdown(question)

        # Get answer from Claude
        with st.chat_message("assistant"):
            with st.spinner("Searching rules and generating answer..."):
                try:
                    result = st.session_state.qa_system.answer_question(question)

                    answer = result['answer']
                    st.markdown(answer)

                    # Add rules last updated info
                    if result.get('rules_last_updated'):
                        last_update = datetime.fromisoformat(result['rules_last_updated'])
                        st.caption(f"*Rules last updated: {last_update.strftime('%B %d, %Y')}*")

                    # Store in chat history with metadata
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "metadata": result
                    })

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })


def course_search_page():
    """Golf course search and filter page."""
    st.markdown('<div class="main-header">🏌️ Golf Course Finder</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Find courses by location and difficulty</div>', unsafe_allow_html=True)

    # Search filters
    st.markdown("### 🔍 Search Filters")

    col1, col2 = st.columns(2)

    with col1:
        city = st.text_input("City", placeholder="e.g., Pebble Beach")
        state = st.text_input("State (2-letter code)", placeholder="e.g., CA", max_chars=2)

    with col2:
        # Slope rating filter
        st.markdown("**Slope Rating Range** (55-155)")
        difficulty_level = st.select_slider(
            "Difficulty Level",
            options=["Beginner (55-110)", "Intermediate (111-130)", "Advanced (131-155)", "All"],
            value="All"
        )

        # Map difficulty to slope range
        slope_ranges = {
            "Beginner (55-110)": (55, 110),
            "Intermediate (111-130)": (111, 130),
            "Advanced (131-155)": (131, 155),
            "All": (55, 155)
        }
        slope_min, slope_max = slope_ranges[difficulty_level]

    # Search button
    if st.button("🔍 Search Courses", type="primary"):
        with st.spinner("Searching courses..."):
            # Search database
            courses = st.session_state.db.search_courses(
                city=city if city else None,
                state=state.upper() if state else None,
                slope_min=slope_min,
                slope_max=slope_max,
                limit=50
            )

            if courses:
                st.success(f"Found {len(courses)} courses")

                # Display results
                for course in courses:
                    with st.container():
                        st.markdown(f"### {course['name']}")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown(f"**📍 Location:**")
                            location_parts = [course['city'], course['state'], course['zip_code']]
                            location = ", ".join(filter(None, location_parts))
                            st.markdown(location)

                        with col2:
                            st.markdown(f"**⛰️ Slope Rating:**")
                            st.markdown(f"{course['slope_rating_min']} - {course['slope_rating_max']}")

                        with col3:
                            st.markdown(f"**⭐ Course Rating:**")
                            st.markdown(f"{course['course_rating_min']:.1f} - {course['course_rating_max']:.1f}")

                        # Tee details
                        if course['tee_details']:
                            with st.expander("🎯 View Tee Details"):
                                tee_data = []
                                for tee_name, tee_info in course['tee_details'].items():
                                    tee_data.append({
                                        'Tee': tee_name,
                                        'Yardage': tee_info.get('yardage', 'N/A'),
                                        'Par': tee_info.get('par', 'N/A'),
                                        'Course Rating': tee_info.get('course_rating', 'N/A'),
                                        'Slope Rating': tee_info.get('slope_rating', 'N/A'),
                                    })
                                st.dataframe(pd.DataFrame(tee_data), use_container_width=True)

                        # Contact info
                        contact_parts = []
                        if course['phone']:
                            contact_parts.append(f"📞 {course['phone']}")
                        if course['website']:
                            contact_parts.append(f"🌐 [Website]({course['website']})")

                        if contact_parts:
                            st.markdown(" | ".join(contact_parts))

                        # Last updated
                        if course['last_updated']:
                            last_update = datetime.fromisoformat(course['last_updated'])
                            st.caption(f"*Last updated: {last_update.strftime('%B %d, %Y')}*")

                        st.markdown("---")

            else:
                st.warning("No courses found matching your criteria. Try adjusting your filters.")


def analytics_page():
    """Analytics and metrics dashboard."""
    st.markdown('<div class="main-header">📊 Analytics Dashboard</div>', unsafe_allow_html=True)

    # Time period selector
    days = st.selectbox("Time Period", [7, 30, 90], index=1)

    # Query statistics
    st.markdown("### 📈 Query Statistics")
    query_stats = st.session_state.db.get_query_stats(days=days)

    if query_stats and query_stats.get('total_queries', 0) > 0:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Queries", int(query_stats['total_queries']))

        with col2:
            avg_time = query_stats['avg_response_time']
            st.metric("Avg Response Time", f"{int(avg_time)}ms" if avg_time else "N/A")

        with col3:
            total_cost = query_stats['total_cost']
            st.metric("Total Cost", f"${total_cost:.2f}" if total_cost else "$0.00")

        with col4:
            feedback_rate = query_stats.get('positive_feedback_rate', 0)
            st.metric("Positive Feedback", f"{feedback_rate * 100:.1f}%" if feedback_rate else "N/A")

    else:
        st.info("No query data available for the selected period.")

    # RAG Metrics
    st.markdown("### 🎯 RAG Evaluation Metrics")
    rag_metrics = st.session_state.db.get_avg_rag_metrics(days=days)

    if rag_metrics and rag_metrics.get('total_evaluations', 0) > 0:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Context Quality**")
            st.metric("Context Relevancy", f"{rag_metrics.get('avg_context_relevancy', 0):.3f}")
            st.metric("Context Precision", f"{rag_metrics.get('avg_context_precision', 0):.3f}")

        with col2:
            st.markdown("**Answer Quality**")
            st.metric("Answer Relevancy", f"{rag_metrics.get('avg_answer_relevancy', 0):.3f}")
            st.metric("Faithfulness", f"{rag_metrics.get('avg_faithfulness', 0):.3f}")
            st.metric("Cosine Similarity", f"{rag_metrics.get('avg_cosine_similarity', 0):.3f}")

        st.caption(f"*Based on {int(rag_metrics['total_evaluations'])} evaluations*")

    else:
        st.info("No RAG metrics available yet. Metrics are collected as queries are processed.")

    # API Cost Breakdown
    st.markdown("### 💰 API Cost Breakdown")
    api_costs = st.session_state.db.get_api_costs(days=days)

    if api_costs:
        cost_data = []
        for api_name, data in api_costs.items():
            cost_data.append({
                'API': api_name.title(),
                'Total Cost': f"${data['cost']:.4f}",
                'Total Tokens': f"{int(data['tokens']):,}"
            })

        st.dataframe(pd.DataFrame(cost_data), use_container_width=True)
    else:
        st.info("No API usage data available.")


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()

    # Initialize app
    initialize_app()

    # Sidebar navigation
    st.sidebar.title("⛳ Golf App")

    page = st.sidebar.radio(
        "Navigation",
        ["Rules Q&A", "Course Finder", "Analytics"],
        label_visibility="collapsed"
    )

    # Display data freshness
    display_data_freshness()

    # Add info section
    with st.sidebar.expander("ℹ️ About"):
        st.markdown("""
        **Golf Rules Q&A & Course Finder**

        This app helps golfers:
        - Get instant answers to rules questions
        - Find courses by difficulty level
        - Track data freshness and quality

        **Powered by:**
        - Anthropic Claude AI
        - RAG (Retrieval-Augmented Generation)
        - USGA Rules of Golf
        """)

    # Route to appropriate page
    if page == "Rules Q&A":
        rules_qa_page()
    elif page == "Course Finder":
        course_search_page()
    elif page == "Analytics":
        analytics_page()


if __name__ == "__main__":
    main()
