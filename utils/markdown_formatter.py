"""
Markdown Formatter for AI Consultation Output
Converts Markdown to beautifully formatted HTML with cards, grids, tables, and stat boxes
"""

import re
import markdown
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple

def format_consultation_output(markdown_text: str, lang: str = 'ar') -> str:
    """
    Convert Markdown AI output to beautifully formatted HTML
    
    Args:
        markdown_text: Raw Markdown text from AI
        lang: Language code ('ar' or 'en')
    
    Returns:
        Formatted HTML string with cards, grids, tables, and stat boxes
    """
    if not markdown_text:
        return ""
    
    # Convert Markdown to HTML using markdown library
    md = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'nl2br',
        'sane_lists'
    ])
    html = md.convert(markdown_text)
    
    # Parse HTML with BeautifulSoup for transformation
    soup = BeautifulSoup(html, 'html.parser')
    
    # Transform lists to cards (3+ items)
    _transform_lists_to_cards(soup, lang)
    
    # Extract and format stat boxes
    _extract_stat_boxes(soup)
    
    # Transform key-value patterns to info grids
    _transform_info_grids(soup, lang)
    
    # Enhance tables
    _enhance_tables(soup, lang)
    
    # Add responsive classes to images
    for img in soup.find_all('img'):
        img['class'] = img.get('class', []) + ['img-fluid', 'rounded']
    
    return str(soup)


def _transform_lists_to_cards(soup: BeautifulSoup, lang: str) -> None:
    """Add card-list class to lists with 3+ items (matches JS logic exactly)"""
    for ul in soup.find_all('ul'):
        items = ul.find_all('li', recursive=False)
        
        # If list has 3+ items and doesn't have 'no-cards' class, add 'card-list' class
        if len(items) >= 3 and 'no-cards' not in ul.get('class', []):
            # Add card-list class (don't replace HTML structure)
            classes = ul.get('class', [])
            if 'card-list' not in classes:
                classes.append('card-list')
                ul['class'] = classes


def _extract_stat_boxes(soup: BeautifulSoup) -> None:
    """Extract and format statistics (matches JS logic exactly)"""
    # Exact pattern from JS: /^(\d+[%$]?|\$?\d+(?:,\d{3})*(?:\.\d+)?)\s*[-:–]\s*(.+)$/
    stat_pattern = re.compile(r'^(\d+[%$]?|\$?\d+(?:,\d{3})*(?:\.\d+)?)\s*[-:–]\s*(.+)$')
    
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        match = stat_pattern.match(text)
        
        if match and match.group(1) and match.group(2):
            # Create stat box with span elements (not div)
            stat_box = soup.new_tag('div', **{'class': 'stat-box'})
            
            # Use span tags like JS does
            number_tag = soup.new_tag('span', **{'class': 'stat-number'})
            number_tag.string = match.group(1)
            stat_box.append(number_tag)
            
            label_tag = soup.new_tag('span', **{'class': 'stat-label'})
            label_tag.string = match.group(2).strip()
            stat_box.append(label_tag)
            
            # Replace paragraph with stat box
            p.replace_with(stat_box)


def _transform_info_grids(soup: BeautifulSoup, lang: str) -> None:
    """Transform key-value patterns into info grids (matches JS logic exactly)"""
    # Find all <strong> elements and check for : or - pattern
    grid_items = []
    
    for strong in soup.find_all('strong'):
        # Check next sibling for text node starting with : or -
        next_sibling = strong.next_sibling
        if next_sibling and isinstance(next_sibling, str):  # Text node
            text = next_sibling.strip()
            if text.startswith(':') or text.startswith('-'):
                value = text[1:].strip()
                parent = strong.parent
                
                grid_items.append({
                    'label': strong.get_text(),
                    'value': value,
                    'element': parent,
                    'strong': strong
                })
    
    # If we found 3+ items, create info-grid container
    if len(grid_items) >= 3:
        # Create grid container
        grid_container = soup.new_tag('div', **{'class': 'info-grid'})
        first_element = grid_items[0]['element']
        
        for item in grid_items:
            # Create grid item with exact JS structure
            grid_item = soup.new_tag('div', **{'class': 'info-grid-item'})
            
            # Add strong tag
            strong_tag = soup.new_tag('strong')
            strong_tag.string = item['label']
            grid_item.append(strong_tag)
            
            # Add p tag with value
            p_tag = soup.new_tag('p')
            p_tag.string = item['value']
            grid_item.append(p_tag)
            
            grid_container.append(grid_item)
            
            # Remove original element
            if item['element'] and item['element'].parent:
                item['element'].decompose()
        
        # Insert grid before first element's position
        if first_element and first_element.parent:
            first_element.parent.insert(0, grid_container)
        else:
            # Fallback: insert at beginning of body
            body = soup.find('body') or soup
            body.insert(0, grid_container)


def _enhance_tables(soup: BeautifulSoup, lang: str) -> None:
    """Wrap tables in responsive containers (matches JS logic exactly)"""
    for table in soup.find_all('table'):
        # Only wrap if not already wrapped
        if not table.parent or not table.parent.has_attr('class') or 'table-responsive' not in table.parent.get('class', []):
            # Create wrapper div
            wrapper = soup.new_tag('div', **{'class': 'table-responsive'})
            
            # Insert wrapper before table and move table into wrapper
            table.insert_before(wrapper)
            wrapper.append(table)


def clean_markdown_for_excel(markdown_text: str) -> str:
    """
    Clean Markdown text for Excel export
    Removes Markdown symbols while preserving structure
    
    Args:
        markdown_text: Raw Markdown text
    
    Returns:
        Clean text suitable for Excel
    """
    if not markdown_text:
        return ""
    
    # Remove bold/italic markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', markdown_text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Convert headers to plain text with spacing
    text = re.sub(r'^###\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s+(.+)$', r'\n\n\1\n', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s+(.+)$', r'\n\n\1\n\n', text, flags=re.MULTILINE)
    
    # Remove code markers
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'```[\w]*\n', '', text)
    text = re.sub(r'```', '', text)
    
    # Clean up links [text](url) -> text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n\n\n+', '\n\n', text)
    
    return text.strip()


def extract_sections_from_markdown(markdown_text: str) -> List[Dict[str, str]]:
    """
    Extract sections from Markdown for structured Excel export
    
    Args:
        markdown_text: Raw Markdown text
    
    Returns:
        List of sections with title and content
    """
    sections = []
    
    if not markdown_text:
        return sections
    
    # Split by top-level headers (##)
    parts = re.split(r'^##\s+(.+)$', markdown_text, flags=re.MULTILINE)
    
    if len(parts) > 1:
        # First part is intro (before first header)
        if parts[0].strip():
            sections.append({
                'title': 'مقدمة' if 'العر' in markdown_text[:100] else 'Introduction',
                'content': parts[0].strip()
            })
        
        # Process remaining parts (title, content pairs)
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                sections.append({
                    'title': parts[i].strip(),
                    'content': parts[i + 1].strip()
                })
    else:
        # No headers, treat as single section
        sections.append({
            'title': 'المحتوى' if 'العر' in markdown_text[:100] else 'Content',
            'content': markdown_text
        })
    
    return sections
