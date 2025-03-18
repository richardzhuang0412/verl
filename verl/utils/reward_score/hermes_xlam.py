import re
import ast
import json

from difflib import SequenceMatcher

def compare_sequences(seq1, seq2):
    """Compare two sequences and return similarity ratio between 0 and 1"""
    matcher = SequenceMatcher(None, seq1, seq2)
    return matcher.ratio()

def extract_assistant_response(solution_str):
    """Extract the assistant's response from the full conversation"""
    return solution_str.split("<|im_start|>assistant")[-1].split("<|endoftext|>")[0]

def format_check(solution_str):
    """Check if solution follows the expected format and return appropriate score"""
    thought_pattern = r'<\|begin_of_thought\|>(.*?)<\|end_of_thought\|>'
    solution_pattern = r'<\|begin_of_solution\|>(.*?)<\|end_of_solution\|>'
    
    thought_match = re.search(thought_pattern, solution_str, re.DOTALL)
    solution_match = re.search(solution_pattern, solution_str, re.DOTALL)
    
    if thought_match and solution_match:
        return 0, solution_match.group(1).strip()
    elif thought_match:
        return -0.5, None
    elif solution_match:
        return -0.5, solution_match.group(1).strip()
    else: # Nothing matched
        return -1, None

def content_check(solution_str, ground_truth, content_incorrect_score=0, content_correct_score=1.0):
    """Check the content of the solution against ground truth"""
    try:
        ground_truth = json.loads(ground_truth)
        is_xlam = True
    except:
        is_xlam = False

    if (is_xlam) or ('<tool_call>' in ground_truth):
        # Extract tool calls from ground truth
        if is_xlam:
            gt_dicts = ground_truth if isinstance(ground_truth, list) else [ground_truth]
        else:
            gt_tool_calls = re.findall(r'<tool_call>(.*?)</tool_call>', ground_truth, re.DOTALL)
            gt_dicts = []
            for call in gt_tool_calls:
                try:
                    gt_dicts.append(ast.literal_eval(call.strip()))
                except:
                    raise ValueError(f"Debug: Problem with ground truth: {call}")
        
        # Extract tool calls from solution
        solution_tool_calls = re.findall(r'<tool_call>(.*?)</tool_call>', solution_str, re.DOTALL)
        solution_dicts = []
        
        # Check if there's non-trivial content besides tool calls
        # solution_without_calls = re.sub(r'<tool_call>.*?</tool_call>', '', solution_str, flags=re.DOTALL)
        # solution_without_calls = solution_without_calls.replace('\\n', '').strip()
        # if solution_without_calls != '':
        #     print(f"Found non-trivial content besides tool calls: {solution_str}")
        #     return -0.5
            
        for call in solution_tool_calls:
            try:
                call = call.replace('\\n', '').strip()
                solution_dicts.append(ast.literal_eval(call))
            except:
                return content_incorrect_score
        
        # Compare lengths
        if len(gt_dicts) != len(solution_dicts):
            return content_incorrect_score
        # elif len(gt_dicts) < len(solution_dicts):
        #     return content_incorrect_score - 0.5 # Penalty for over-generating function calls
        
        # Compare each dictionary recursively
        def compare_dicts(dict1, dict2):
            if not isinstance(dict1, dict) or not isinstance(dict2, dict):
                return dict1 == dict2
            
            if set(dict1.keys()) != set(dict2.keys()):
                return False
            
            for key in dict1:
                if not compare_dicts(dict1[key], dict2[key]):
                    return False
            return True
        
        # Compare each pair of dictionaries in order
        for gt_dict, solution_dict in zip(gt_dicts, solution_dicts):
            if not compare_dicts(gt_dict, solution_dict):
                return content_incorrect_score
        
        return content_correct_score
    else:
        # Ground truth is natural language
        # Check solution doesn't contain tool calls
        if '<tool_call>' in solution_str:
            return content_incorrect_score
        else:
            similarity_score = compare_sequences(solution_str, ground_truth)
            # Apply thresholding
            # if similarity_score > 0.5:
            #     similarity_score = 1.0
            # else:
            #     similarity_score = 0.0
            return similarity_score

def compute_score(solution_str, ground_truth, content_incorrect_score=0, content_correct_score=1.0):
    # print(f"Original solution: {solution_str}")

    # Extract assistant response
    assistant_response = extract_assistant_response(solution_str)
    # print(f"Assistant response: {assistant_response}")

    # Check format
    format_score, extracted_solution = format_check(assistant_response)
    if extracted_solution == None:
        return format_score
    # print(f"Extracted solution: {extracted_solution}")
    # print(f"Format score: {format_score}")

    # Check content
    content_score = content_check(extracted_solution, ground_truth, content_incorrect_score, content_correct_score)
    if content_score != 1 and content_score != 0:
        raise ValueError(f"Debug: Content score: {content_score}, extracted solution: {extracted_solution}, ground truth: {ground_truth}")
    # print(f"Content score: {content_score}")
    total_score = format_score + content_score
    # print(f"Total score: {total_score}")
    # raise ValueError(f"Debug")
    return total_score

# def compute_score(solution_str, ground_truth, content_incorrect_score=0, content_correct_score=1.0):
#     # print(f"Original solution: {solution_str}")

#     # Extract assistant response
#     assistant_response = extract_assistant_response(solution_str)
#     # print(f"Assistant response: {assistant_response}")

#     # Check format
#     format_score, extracted_solution = format_check(assistant_response)
#     if extracted_solution == None:
#         return 0
#     # print(f"Extracted solution: {extracted_solution}")
#     # print(f"Format score: {format_score}")

#     # Check content
#     content_score = content_check(extracted_solution, ground_truth, content_incorrect_score, content_correct_score)
#     if content_score == 1:
#         return 1
#     elif content_score == 0:
#         return 0
#     else:
#         raise ValueError(f"Debug: Content score: {content_score}")

#     # print(f"Content score: {content_score}")
#     total_score = format_score + content_score
#     # print(f"Total score: {total_score}")
#     # raise ValueError(f"Debug")
#     return total_score





# if __name__ == "__main__":
#     solution_str = "Hello, how are you?"
#     ground_truth = "Hello, how are you?"
#     print(compare_sequences(solution_str, ground_truth))