import json
import os
import javalang
from javalang.tree import MethodDeclaration, Annotation, ElementArrayValue, VoidClassReference


def process_java_file(file_path):
    if "ToolResource" in file_path:
        return

    with open(file_path, 'r', newline="", encoding='utf-8') as f:
        content = f.read()

    try:
        tree = javalang.parse.parse(content)
    except Exception as e:
        print(f"解析文件 {file_path} 失败: {e}")
        return

    modified = False
    lines = content.split('\n')
    print(file_path)
    for path, node in tree.filter(MethodDeclaration):
        if not node.annotations:
            continue

        for annotation in node.annotations:
            if annotation.name == 'Operation':
                responses = None
                for element in annotation.element:
                    if element.name == 'responses':
                        responses = element.value
                        break

                if responses and isinstance(responses, ElementArrayValue):
                    values = responses.values
                    for response in values:
                        if hasattr(response, 'name') and response.name == 'ApiResponse':
                            content_annotation = None
                            for elem in response.element:
                                if elem.name == 'content':
                                    content_annotation = elem.value
                                    break

                            if content_annotation and hasattr(content_annotation, 'name') and content_annotation.name == 'Content':
                                schema = None
                                for elem in content_annotation.element:
                                    if elem.name == 'schema':
                                        schema = elem.value
                                        break

                                if schema and hasattr(schema, 'name') and schema.name == 'Schema':
                                    implementation = None
                                    for elem in schema.element:
                                        if elem.name == 'implementation':
                                            implementation = elem.value
                                            break

                                    if implementation:
                                        line_num = response.position.line - 1
                                        line = lines[line_num]
                                        insert_pos = line.find("@ApiResponse(")
                                        if insert_pos > 0 and "description" not in lines[line_num]:
                                            if isinstance(implementation, VoidClassReference):
                                                new_desc = f'description = "void"'
                                            else:
                                                new_desc = f'description = "{implementation.type.name}"'
                                            new_line = line[:insert_pos+len("@ApiResponse(")] + f'{new_desc}, ' + line[insert_pos+len("@ApiResponse("):]
                                            lines[line_num] = new_line
                                            modified = True
                                        # description = str(implementation).split('.')[-1].replace('class', '').strip()
                                        # for elem in response.element:
                                        #     if elem.name == 'description':
                                        #         # Update the line with new description
                                        #         line_num = elem.position.line - 1
                                        #         lines[line_num] = f'description = "{description}"'
                                        #         modified = True
                                        #         break
                                        # 找到方法声明的行号
                                        # for i, line in enumerate(lines):
                                        #     if line.strip().startswith('@Operation'):
                                        #         # 生成新的description
                                        #         new_desc = f'description = "{implementation.type.name}"'
                                        #         if 'description =' not in line:
                                        #             # 添加description
                                        #             line = str(line)
                                        #             insert_index = line.find("@ApiResponse(")
                                        #             lines[i] = line[:insert_index+len("@ApiResponse(")] + f'{new_desc}, ' + line[insert_index++len("@ApiResponse("):]
                                        #             modified = True
                                        #         break

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"已修改文件: {file_path}")

def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.isdir(file):
                continue
            if file.endswith('.java'):
                process_java_file(os.path.join(root, file))

if __name__ == '__main__':
    process_directory("")