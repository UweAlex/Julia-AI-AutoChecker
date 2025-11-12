import re
from collections import Counter

def lint_julia(code):
    issues = []
    fixed_code = code  # Start with original; apply fixes if needed
    
    # 1. Balanced function/end
    functions = len(re.findall(r'function\s+\w', code))
    ends = len(re.findall(r'^\s*end\s*$', code, re.MULTILINE))
    if functions != ends:
        issues.append(f"Imbalance: {functions} 'function' vs {ends} 'end'")

    # 2. catch syntax
    bad_catches = re.findall(r'catch\s+(?!_|\w+\s*;).*?(?=\n|end)', code, re.DOTALL)
    for bad in bad_catches:
        issues.append(f"Invalid catch: '{bad.strip()}' – use 'catch _;' or 'catch err;'")

    # 3. Quotes balanced (global)
    open_quotes = code.count('"') + code.count("'")
    if open_quotes % 2 != 0:
        issues.append("Unbalanced quotes (odd count)")

    # 4. Multi-char literals
    multi_literals = re.findall(r"'([^']{2,})'", code)
    if multi_literals:
        issues.append(f"Multi-char literals: {multi_literals[:3]}... – use string")

    # 5. Indentation
    lines = code.split('\n')
    indents = [len(re.match(r'^\s*', line).group()) % 4 for line in lines if line.strip()]
    inconsistent = [i for i in set(indents) if i != 0 and i != 4]
    if inconsistent:
        issues.append(f"Inconsistent indentation: {Counter(indents)} – use 4 spaces")

    # 6. Redundant T(0.5)
    redundant_t = re.findall(r'T\([0-9.]+\)', code)
    if redundant_t:
        issues.append(f"Redundant T(0.5): {redundant_t[:3]}... – remove T()")

    # 7. Filter/lambda quote balance
    lambdas = re.findall(r'filter\(tf -> "([^"]*)?" not in .*?\)', code)
    for f in lambdas:
        if not re.search(r'"[^"]*"', f):
            issues.append(f"Vague filter 'not in' for '{f}' – check quotes")

    # 8. Python operators
    python_ops = re.findall(r'\b(and|or|elif|True|False|is not)\b', code)
    if python_ops:
        op_map = {'and': '&&', 'or': '||', 'elif': 'elseif', 'True': 'true', 'False': 'false', 'is not': '!=='}
        op_info = [f"'{op}' (use '{op_map.get(op, "Unknown")}')" for op in sorted(set(python_ops))]
        issues.append(f"Python operators: {', '.join(op_info[:3])}...")

    # 9. Auto-replace "a not in b" to "!(a in b)"
    if 'not in' in code:
        pattern = r'("([^"]*)"|\'([^\']*)\')\s*not\s+in\s*([^;,\)\n]+)'
        fixed = re.sub(pattern, r'!\2 in \4', code)
        if fixed != code:
            issues.append("Auto-fixed 'not in' to '!(... in ...)' – see fixed_code below")
            fixed_code = fixed

    # 10. Invalid @test keywords (label=, description=)
    invalid_test_keywords = re.findall(r'@test\s+.*?\s+(label|description)\s*=\s*', code)
    if invalid_test_keywords:
        issues.append(f"Invalid @test keywords: {set(invalid_test_keywords)} – use string suffix")

    # 11. Unbalanced parentheses
    left_paren = code.count('(')
    right_paren = code.count(')')
    if left_paren != right_paren:
        issues.append(f"Unbalanced parentheses: {left_paren} '(' vs {right_paren} ')'")

    # 12. Unnecessary $(var) in strings
    unnecessary_interp = re.findall(r'\$\(\w+\)', code)
    if unnecessary_interp:
        issues.append(f"Unnecessary $(var) in strings: {unnecessary_interp[:3]}... – use $var")

    # 13. @test with interpolated description: "text $(var)"
    bad_test_desc = re.findall(r'@test\s+[^\n"]+"\s*"\$[({][^"}]*[})]"', code)
    if bad_test_desc:
        issues.append(f"Invalid @test description with $(...): {bad_test_desc[:2]}... – use $var in literal string")

    if issues:
        return f"Fixes ({len(issues)}):\n" + '\n'.join(f"- {i}" for i in issues[:10]) + f"\n\nFixed code:\n{fixed_code}"
    return f"Clean! Ready for Julia.\n\nCode:\n{code}"

# CLI
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == '-':
            code = sys.stdin.read()
        else:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                code = f.read()
        print(lint_julia(code))
    else:
        print("Usage: python lint_julia.py [file.jl] or | python lint_julia.py -")
