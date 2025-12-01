"""
SCM Migration Parser
Converts Palo Alto configuration compatibility JSON files into readable HTML reports.
"""

import json
import sys
import xml.etree.ElementTree as ET
from html import escape


def load_json_file(filepath):
    """Load and parse JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{filepath}': {e}")
        sys.exit(1)


def load_xml_file(filepath):
    """Load and parse XML configuration file."""
    if not filepath:
        return None
    
    try:
        tree = ET.parse(filepath)
        return tree.getroot()
    except FileNotFoundError:
        print(f"Warning: XML file '{filepath}' not found. Continuing without XML extraction.")
        return None
    except ET.ParseError as e:
        print(f"Warning: Invalid XML in '{filepath}': {e}. Continuing without XML extraction.")
        return None


def extract_xml_from_xpath(root, xpath):
    """Extract XML content from the given XPath."""
    if root is None:
        return None
    
    try:
        # Parse the XPath and navigate to the element
        # XPath format: /devices/entry[@name="..."]/template/entry[@name="..."]/...
        parts = [p for p in xpath.split('/') if p]
        current = root
        
        for part in parts:
            if 'entry[@name=' in part:
                # Extract the name attribute value
                import re
                match = re.search(r'entry\[@name="([^"]+)"\]', part)
                if match:
                    name_value = match.group(1)
                    # Find entry with matching name attribute
                    found = False
                    for child in current:
                        if child.tag == 'entry' and child.get('name') == name_value:
                            current = child
                            found = True
                            break
                    if not found:
                        return None
                else:
                    return None
            else:
                # Simple tag name
                found = False
                for child in current:
                    if child.tag == part:
                        current = child
                        found = True
                        break
                if not found:
                    return None
        
        # Convert the found element to a pretty XML string
        return ET.tostring(current, encoding='unicode', method='xml')
    except Exception as e:
        # Return None if extraction fails
        return None


def pretty_print_xml(xml_string):
    """Format XML string with proper indentation."""
    if not xml_string:
        return None
    
    try:
        # Parse and re-format the XML
        elem = ET.fromstring(xml_string)
        ET.indent(elem, space='  ')
        return ET.tostring(elem, encoding='unicode', method='xml')
    except:
        # If pretty printing fails, return original
        return xml_string


def format_xpath(xpath):
    """Format XPath to look more like a readable file path."""
    # Remove the leading slash and split
    xpath = xpath.strip('/')
    parts = xpath.split('/')
    
    # Clean up entry[@name="..."] to just show the name
    formatted_parts = []
    for part in parts:
        if 'entry[@name=' in part:
            # Extract just the name value
            import re
            match = re.search(r'entry\[@name="([^"]+)"\]', part)
            if match:
                formatted_parts.append(match.group(1))
            else:
                formatted_parts.append(part)
        else:
            formatted_parts.append(part)
    
    # Join with forward slashes to look like a path
    return '/' + '/'.join(formatted_parts)


def generate_summary_table(data):
    """Generate summary table from all details sections."""
    all_items = []
    
    # Collect all items from Unsupported Features, Unsupported Flags, and Blocking Features
    for section in data:
        category = section.get('category', '')
        if category in ['Unsupported Features', 'Unsupported Flags', 'Blocking Features']:
            details = section.get('details', [])
            for item in details:
                # Create a clean copy without referenced-in fields
                summary_item = {
                    'category': category,
                    'rule-id': item.get('rule-id', 'N/A'),
                    'description': item.get('description', 'N/A'),
                    'feature': item.get('feature', 'N/A'),
                    'tag': item.get('tag', 'N/A'),
                    'group': item.get('group', 'N/A'),
                    'count': item.get('count', 0),
                    'location': item.get('location', 'N/A')
                }
                all_items.append(summary_item)
    
    if not all_items:
        return '<p class="no-issues">No issues found in configuration.</p>'
    
    # Generate table
    html = '''
    <div class="table-container">
        <table class="summary-table">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Rule ID</th>
                    <th>Description</th>
                    <th>Feature</th>
                    <th>Tag</th>
                    <th>Group</th>
                    <th>Count</th>
                    <th>Location</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for item in all_items:
        category_class = ''
        if item['category'] == 'Unsupported Features':
            category_class = 'category-unsupported'
        elif item['category'] == 'Unsupported Flags':
            category_class = 'category-flags'
        elif item['category'] == 'Blocking Features':
            category_class = 'category-blocking'
        
        html += f'''
                <tr class="{category_class}">
                    <td class="category-cell">{escape(item['category'])}</td>
                    <td class="rule-id-cell">{escape(item['rule-id'])}</td>
                    <td class="description-cell">{escape(item['description'])}</td>
                    <td>{escape(item['feature'])}</td>
                    <td>{escape(item['tag'])}</td>
                    <td>{escape(item['group'])}</td>
                    <td class="count-cell">{item['count']}</td>
                    <td>{escape(item['location'])}</td>
                </tr>
        '''
    
    html += '''
            </tbody>
        </table>
    </div>
    '''
    
    return html


def generate_unsupported_features_section(details, xml_root=None):
    """Generate HTML for unsupported features section."""
    if not details:
        return '<p class="no-issues">No unsupported features found.</p>'
    
    html = '<div class="details-grid">'
    
    for item in details:
        html += f'''
        <div class="detail-card unsupported">
            <div class="detail-header">
                <h4>{escape(item.get('description', 'N/A'))}</h4>
                <span class="badge badge-error">Unsupported</span>
            </div>
            <div class="detail-content">
                <div class="info-row">
                    <span class="label">Rule ID:</span>
                    <span class="value">{escape(item.get('rule-id', 'N/A'))}</span>
                </div>
                <div class="info-row">
                    <span class="label">Feature:</span>
                    <span class="value">{escape(item.get('feature', 'N/A'))}</span>
                </div>
                <div class="info-row">
                    <span class="label">Tag:</span>
                    <span class="value">{escape(item.get('tag', 'N/A'))}</span>
                </div>
                <div class="info-row">
                    <span class="label">Group:</span>
                    <span class="value">{escape(item.get('group', 'N/A'))}</span>
                </div>
                <div class="info-row">
                    <span class="label">Count:</span>
                    <span class="value count">{item.get('count', 0)}</span>
                </div>
                <div class="info-row">
                    <span class="label">Location:</span>
                    <span class="value">{escape(item.get('location', 'N/A'))}</span>
                </div>
        '''
        
        # Referenced templates
        ref_in = item.get('referenced-in', {})
        if ref_in.get('templates'):
            html += '<div class="referenced-section">'
            html += '<h5>Referenced in Templates:</h5>'
            html += '<ul class="template-list">'
            for template in ref_in['templates']:
                html += f'<li>{escape(template)}</li>'
            html += '</ul></div>'
        
        # XPaths
        ref_xpaths = item.get('referenced-in-with-xpaths', {})
        if ref_xpaths.get('templates'):
            html += '<div class="xpath-section">'
            html += '<h5>Configuration Paths:</h5>'
            for template, xpaths in ref_xpaths['templates'].items():
                html += f'<div class="xpath-template"><strong>{escape(template)}:</strong></div>'
                html += '<ul class="xpath-list">'
                for xpath in xpaths:
                    formatted_xpath = format_xpath(xpath)
                    html += f'<li class="xpath-item">{formatted_xpath}'
                    
                    # Extract and display actual XML content if available
                    if xml_root is not None:
                        xml_content = extract_xml_from_xpath(xml_root, xpath)
                        if xml_content:
                            pretty_xml = pretty_print_xml(xml_content)
                            if pretty_xml:
                                html += '<div class="xml-content">'
                                html += '<div class="xml-content-header">Configuration XML:</div>'
                                html += f'<pre class="xml-code">{escape(pretty_xml)}</pre>'
                                html += '</div>'
                    
                    html += '</li>'
                html += '</ul>'
            html += '</div>'
        
        html += '</div></div>'
    
    html += '</div>'
    return html


def generate_unsupported_flags_section(details, xml_root=None):
    """Generate HTML for unsupported flags section."""
    if not details:
        return '<p class="no-issues">No unsupported flags found.</p>'
    
    return generate_unsupported_features_section(details, xml_root)


def generate_blocking_features_section(details, xml_root=None):
    """Generate HTML for blocking features section."""
    if not details:
        return '<p class="success">No blocking features found.</p>'
    
    return generate_unsupported_features_section(details, xml_root)


def generate_config_summary_section(details):
    """Generate HTML for configuration summary section."""
    if not details:
        return '<p>No configuration summary available.</p>'
    
    html = '<div class="summary-grid">'
    
    for item in details:
        desc = escape(str(item.get('description', 'N/A')))
        count = escape(str(item.get('count', 'N/A')))
        
        html += f'''
        <div class="summary-item">
            <span class="summary-label">{desc}:</span>
            <span class="summary-value">{count}</span>
        </div>
        '''
    
    html += '</div>'
    return html


def generate_templates_section(details):
    """Generate HTML for templates section."""
    if not details:
        return '<p>No template details available.</p>'
    
    html = '<div class="templates-grid">'
    
    for template_name, template_data in details.items():
        html += f'''
        <div class="template-card">
            <h4 class="template-name">{escape(template_name)}</h4>
        '''
        
        # Unsupported features
        unsupported = template_data.get('unsupported-drop', [])
        if unsupported:
            html += '<div class="template-section">'
            html += '<h5 class="section-title unsupported-title">Unsupported Features:</h5>'
            html += '<ul class="feature-list unsupported-list">'
            for feature in unsupported:
                html += f'<li>{escape(feature)}</li>'
            html += '</ul></div>'
        
        # Supported but dropped features
        supported = template_data.get('supported-drop', [])
        if supported:
            html += '<div class="template-section">'
            html += '<h5 class="section-title supported-title">Supported but Dropped:</h5>'
            html += '<ul class="feature-list supported-list">'
            for feature in supported:
                html += f'<li>{escape(feature)}</li>'
            html += '</ul></div>'
        
        html += '</div>'
    
    html += '</div>'
    return html


def generate_device_group_tree(group, level=0):
    """Recursively generate HTML for device group hierarchy."""
    indent = level * 20
    
    # Determine status class
    total_unsupported = group.get('total-unsupported', 0)
    total_partial = group.get('total-partially-supported', 0)
    
    if total_unsupported > 0:
        status_class = 'has-unsupported'
        status_badge = f'<span class="badge badge-error">{total_unsupported} unsupported</span>'
    elif total_partial > 0:
        status_class = 'has-partial'
        status_badge = f'<span class="badge badge-warning">{total_partial} partial</span>'
    else:
        status_class = 'has-none'
        status_badge = '<span class="badge badge-success">All supported</span>'
    
    html = f'<div class="device-group {status_class}" style="margin-left: {indent}px;">'
    html += f'<div class="group-header">'
    html += f'<h4 class="group-name">{escape(group.get("name", "Unknown"))}</h4>'
    html += status_badge
    html += '</div>'
    
    # Show devices, templates, template-stacks if present
    if group.get('devices'):
        html += '<div class="group-info">'
        html += '<strong>Devices:</strong> ' + ', '.join(escape(d) for d in group['devices'])
        html += '</div>'
    
    if group.get('template-stacks'):
        html += '<div class="group-info">'
        html += '<strong>Template Stacks:</strong> ' + ', '.join(escape(t) for t in group['template-stacks'])
        html += '</div>'
    
    if group.get('templates'):
        html += '<div class="group-info">'
        html += '<strong>Templates:</strong> ' + ', '.join(escape(t) for t in group['templates'])
        html += '</div>'
    
    html += '</div>'
    
    # Process children recursively
    children = group.get('children', [])
    if children:
        for child in children:
            html += generate_device_group_tree(child, level + 1)
    
    return html


def generate_device_groups_section(details):
    """Generate HTML for device groups section."""
    if not details:
        return '<p>No device group details available.</p>'
    
    html = '<div class="device-groups-container">'
    
    for group in details:
        html += generate_device_group_tree(group)
    
    html += '</div>'
    return html


def generate_html_report(data, xml_root=None):
    """Generate complete HTML report from JSON data."""
    
    # Extract sections
    sections = {}
    for section in data:
        category = section.get('category', 'Unknown')
        sections[category] = section.get('details', [])
    
    # Build table of contents entries
    toc_entries = []
    if any(sections.get(cat) for cat in ['Unsupported Features', 'Unsupported Flags', 'Blocking Features']):
        toc_entries.append(('summary', 'Summary of Issues'))
    if sections.get('Unsupported Features'):
        toc_entries.append(('unsupported-features', 'Unsupported Features'))
    if sections.get('Unsupported Flags'):
        toc_entries.append(('unsupported-flags', 'Unsupported Flags'))
    if sections.get('Blocking Features'):
        toc_entries.append(('blocking-features', 'Blocking Features'))
    if sections.get('Configuration Summary'):
        toc_entries.append(('config-summary', 'Configuration Summary'))
    if sections.get('Templates'):
        toc_entries.append(('templates', 'Templates'))
    if 'Template-stacks' in sections:
        toc_entries.append(('template-stacks', 'Template Stacks'))
    if sections.get('Device Groups'):
        toc_entries.append(('device-groups', 'Device Groups'))
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SCM Migration Compatibility Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
            border-bottom: 4px solid #3498db;
            padding-bottom: 10px;
        }}
        
        .report-meta {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 0.9em;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.8em;
            padding: 10px;
            background: #ecf0f1;
            border-left: 5px solid #3498db;
        }}
        
        h3 {{
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.4em;
        }}
        
        h4 {{
            color: #34495e;
            margin-bottom: 10px;
            font-size: 1.2em;
        }}
        
        h5 {{
            color: #555;
            margin-top: 15px;
            margin-bottom: 8px;
            font-size: 1em;
            font-weight: 600;
        }}
        
        .details-grid {{
            display: grid;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .detail-card {{
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 20px;
            background: #fafafa;
        }}
        
        .detail-card.unsupported {{
            border-left: 4px solid #e74c3c;
        }}
        
        .detail-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        
        .detail-content {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .info-row {{
            display: flex;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }}
        
        .label {{
            font-weight: 600;
            color: #555;
            min-width: 120px;
        }}
        
        .value {{
            color: #333;
        }}
        
        .value.count {{
            font-weight: bold;
            color: #e74c3c;
        }}
        
        .badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            white-space: nowrap;
        }}
        
        .badge-error {{
            background: #e74c3c;
            color: white;
        }}
        
        .badge-warning {{
            background: #f39c12;
            color: white;
        }}
        
        .badge-success {{
            background: #27ae60;
            color: white;
        }}
        
        .referenced-section {{
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 4px;
        }}
        
        .template-list {{
            list-style: none;
            margin-top: 8px;
        }}
        
        .template-list li {{
            padding: 6px 12px;
            margin: 4px 0;
            background: #3498db;
            color: white;
            border-radius: 4px;
            display: inline-block;
            margin-right: 8px;
        }}
        
        .xpath-section {{
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        .xpath-section h5 {{
            color: #495057;
            margin-bottom: 10px;
        }}
        
        .xpath-template {{
            margin-top: 12px;
            padding: 8px;
            background: #e9ecef;
            border-radius: 4px;
            color: #0056b3;
            font-weight: 600;
        }}
        
        .xpath-list {{
            list-style: none;
            margin-top: 8px;
        }}
        
        .xpath-item {{
            padding: 8px 12px;
            margin: 6px 0;
            background: white;
            border-left: 3px solid #0056b3;
            border-radius: 4px;
            overflow-x: auto;
            line-height: 1.6;
            color: #212529;
            word-break: break-all;
        }}
        
        .no-issues {{
            padding: 15px;
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
        }}
        
        .success {{
            padding: 15px;
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
            font-weight: 600;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .summary-item {{
            padding: 15px;
            background: #ecf0f1;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #3498db;
        }}
        
        .summary-label {{
            font-weight: 600;
            color: #555;
        }}
        
        .summary-value {{
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .templates-grid {{
            display: grid;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .template-card {{
            border: 2px solid #3498db;
            border-radius: 8px;
            padding: 20px;
            background: #fafafa;
        }}
        
        .template-name {{
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}
        
        .template-section {{
            margin-top: 15px;
        }}
        
        .section-title {{
            margin-bottom: 10px;
        }}
        
        .unsupported-title {{
            color: #e74c3c;
        }}
        
        .supported-title {{
            color: #f39c12;
        }}
        
        .feature-list {{
            list-style: none;
        }}
        
        .feature-list li {{
            padding: 8px 12px;
            margin: 4px 0;
            border-radius: 4px;
        }}
        
        .unsupported-list li {{
            background: #fadbd8;
            border-left: 4px solid #e74c3c;
        }}
        
        .supported-list li {{
            background: #fdeaa3;
            border-left: 4px solid #f39c12;
        }}
        
        .device-groups-container {{
            margin-bottom: 20px;
        }}
        
        .device-group {{
            margin: 10px 0;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #ddd;
        }}
        
        .device-group.has-unsupported {{
            background: #fadbd8;
            border-left: 4px solid #e74c3c;
        }}
        
        .device-group.has-partial {{
            background: #fdeaa3;
            border-left: 4px solid #f39c12;
        }}
        
        .device-group.has-none {{
            background: #d4edda;
            border-left: 4px solid #27ae60;
        }}
        
        .group-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .group-name {{
            color: #2c3e50;
            font-size: 1.1em;
        }}
        
        .group-info {{
            margin: 8px 0;
            padding: 8px;
            background: white;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        
        .group-info strong {{
            color: #555;
        }}
        
        .table-container {{
            margin: 20px 0;
            overflow-x: auto;
        }}
        
        .summary-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .summary-table thead {{
            background: #34495e;
            color: white;
        }}
        
        .summary-table th {{
            padding: 12px 10px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            border-bottom: 2px solid #2c3e50;
        }}
        
        .summary-table td {{
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
            font-size: 0.9em;
        }}
        
        .summary-table tbody tr:hover {{
            background: #f8f9fa;
        }}
        
        .category-unsupported {{
            border-left: 4px solid #e74c3c;
        }}
        
        .category-flags {{
            border-left: 4px solid #f39c12;
        }}
        
        .category-blocking {{
            border-left: 4px solid #c0392b;
        }}
        
        .category-cell {{
            font-weight: 600;
        }}
        
        .rule-id-cell {{
            font-family: 'Courier New', monospace;
            color: #0056b3;
        }}
        
        .description-cell {{
            font-weight: 500;
        }}
        
        .count-cell {{
            font-weight: bold;
            text-align: center;
            color: #e74c3c;
        }}
        
        .toc {{
            background: #f8f9fa;
            border: 2px solid #3498db;
            border-radius: 8px;
            padding: 20px 30px;
            margin: 30px 0;
        }}
        
        .toc h2 {{
            margin-top: 0;
            margin-bottom: 15px;
            background: none;
            border: none;
            padding: 0;
            font-size: 1.5em;
            color: #2c3e50;
        }}
        
        .toc ul {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        
        .toc ul li {{
            margin: 8px 0;
        }}
        
        .toc a {{
            color: #0056b3;
            text-decoration: none;
            padding: 6px 10px;
            display: block;
            border-radius: 4px;
            transition: background-color 0.2s;
        }}
        
        .toc a:hover {{
            background: #e9ecef;
            color: #004085;
        }}
        
        .toc a::before {{
            content: "→ ";
            margin-right: 8px;
            color: #3498db;
        }}
        
        .xml-content {{
            margin-top: 10px;
            padding: 12px;
            background: #1e1e1e;
            border-radius: 4px;
            border: 1px solid #0056b3;
        }}
        
        .xml-content-header {{
            color: #61dafb;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 0.85em;
        }}
        
        .xml-code {{
            margin: 0;
            padding: 12px;
            background: #2d2d2d;
            border-radius: 4px;
            color: #d4d4d4;
            font-family: 'Courier New', Consolas, monospace;
            font-size: 0.85em;
            overflow-x: auto;
            line-height: 1.5;
            white-space: pre;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>SCM Migration Compatibility Report</h1>
        <div class="report-meta">
            Generated on: {escape(str(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')))}
        </div>
        
        <div class="toc">
            <h2>Table of Contents</h2>
            <ul>
'''
    
    # Add TOC links
    for anchor, title in toc_entries:
        html += f'                <li><a href="#{anchor}">{escape(title)}</a></li>\n'
    
    html += '''            </ul>
        </div>
'''
    
    # Generate sections with anchors
    if any(sections.get(cat) for cat in ['Unsupported Features', 'Unsupported Flags', 'Blocking Features']):
        html += '        <h2 id="summary">Summary of Issues</h2>\n'
        html += generate_summary_table(data)
    
    # Generate sections
    if 'Unsupported Features' in sections:
        html += '<h2 id="unsupported-features">Unsupported Features</h2>'
        html += generate_unsupported_features_section(sections['Unsupported Features'], xml_root)
    
    if 'Unsupported Flags' in sections:
        html += '<h2 id="unsupported-flags">Unsupported Flags</h2>'
        html += generate_unsupported_flags_section(sections['Unsupported Flags'], xml_root)
    
    if 'Blocking Features' in sections:
        html += '<h2 id="blocking-features">Blocking Features</h2>'
        html += generate_blocking_features_section(sections['Blocking Features'], xml_root)
    
    if 'Configuration Summary' in sections:
        html += '<h2 id="config-summary">Configuration Summary</h2>'
        html += generate_config_summary_section(sections['Configuration Summary'])
    
    if 'Templates' in sections:
        html += '<h2 id="templates">Templates</h2>'
        html += generate_templates_section(sections['Templates'])
    
    if 'Template-stacks' in sections:
        html += '<h2 id="template-stacks">Template Stacks</h2>'
        if sections['Template-stacks']:
            html += generate_templates_section(sections['Template-stacks'])
        else:
            html += '<p>No template stack details available.</p>'
    
    if 'Device Groups' in sections:
        html += '<h2 id="device-groups">Device Groups</h2>'
        html += generate_device_groups_section(sections['Device Groups'])
    
    html += '''
    </div>
</body>
</html>
'''
    
    return html


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python scm-migration-parser.py <input.json> [output.html] [--xml <panorama-config.xml>]")
        print("Example: python scm-migration-parser.py configuration-compatibility.json report.html --xml panorama-config.xml")
        print("\nOptions:")
        print("  --xml <file>    Optional: Panorama XML configuration file to extract actual XML content")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    xml_file = None
    
    # Parse command line arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--xml' and i + 1 < len(sys.argv):
            xml_file = sys.argv[i + 1]
            i += 2
        elif output_file is None and not sys.argv[i].startswith('--'):
            output_file = sys.argv[i]
            i += 1
        else:
            i += 1
    
    # Auto-generate output filename if not provided
    if output_file is None:
        output_file = input_file.rsplit('.', 1)[0] + '-report.html'
    
    print(f"Loading JSON from: {input_file}")
    data = load_json_file(input_file)
    
    # Load XML if provided
    xml_root = None
    if xml_file:
        print(f"Loading XML configuration from: {xml_file}")
        xml_root = load_xml_file(xml_file)
        if xml_root is not None:
            print("✓ XML configuration loaded successfully")
    
    print("Generating HTML report...")
    html_content = generate_html_report(data, xml_root)
    
    print(f"Writing report to: {output_file}")
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✓ Report generated successfully: {output_file}")
    if xml_root is not None:
        print("  (includes extracted XML content from configuration)")


if __name__ == '__main__':
    main()
