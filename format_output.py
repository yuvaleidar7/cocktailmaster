results = {}
with open('output3.txt', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n\n')

for block in lines:
    if not block.strip(): continue
    lines_b = block.split('\n')
    name = lines_b[0].split(': ')[1]
    match = int(lines_b[1].split(': ')[1].replace('%', ''))
    missing = lines_b[2].split(': ')[1]
    if name not in results or match > results[name]['match']:
        results[name] = {'match': match, 'missing': missing}

sorted_results = sorted(results.items(), key=lambda x: x[1]['match'], reverse=True)

with open('final_output.txt', 'w', encoding='utf-8') as f:
    for name, data in sorted_results:
        f.write(f"- Cocktail Name: {name}\n")
        f.write(f"  Match %: {data['match']}%\n")
        f.write(f"  Missing Ingredients: {data['missing']}\n\n")
