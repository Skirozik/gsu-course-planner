"""
Quick HTML Inspector for GSU Registration Page

Run this to help identify the page structure
"""

print("""
╔════════════════════════════════════════════════════════════════╗
║  GSU Registration Page HTML Inspector                         ║
╚════════════════════════════════════════════════════════════════╝

INSTRUCTIONS:

1. On the GSU registration page with CSC classes showing:
   - Right-click anywhere on the section table
   - Select "Inspect" or "Inspect Element" (or press F12)
   - This opens Developer Tools

2. In the Elements/Inspector tab:
   - Find a row showing a course section
   - Right-click on that HTML element
   - Select "Copy" → "Copy outerHTML"

3. Paste the HTML below and press Enter twice:
""")

print("Paste HTML here, then press Enter twice:")
print("-" * 70)

lines = []
while True:
    try:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    except EOFError:
        break

html_sample = "\n".join(lines[:-1])  # Remove last empty line

if html_sample:
    print("\n" + "="*70)
    print("HTML SAMPLE RECEIVED")
    print("="*70)
    print(html_sample[:500])  # Show first 500 chars
    print("\n...")
    print("\nSaving to file for analysis...")

    with open("gsu_html_sample.html", "w") as f:
        f.write(html_sample)

    print("✅ Saved to: gsu_html_sample.html")
    print("\nNow run: python3 scripts/analyze_gsu_html.py")
else:
    print("No HTML received. Try again!")
