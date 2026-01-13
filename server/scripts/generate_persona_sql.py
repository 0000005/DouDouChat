import json
import os
import sys

def quote_sql(value):
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"

def generate_sql():
    json_path = r'e:\workspace\code\DouDouChat\dev-docs\temp\generated_personas_text.json'
    output_path = r'e:\workspace\code\DouDouChat\server\app\db\init_persona_templates.sql'
    
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found at {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        personas = json.load(f)

    sql_lines = [
        "-- Persona templates generated from generated_personas_text.json",
        "DELETE FROM friend_templates; -- Clear existing templates if any",
        ""
    ]

    for name, data in personas.items():
        # Ensure name consistency
        persona_name = data.get('name', name)
        avatar = data.get('avatar', f"static/avatars/presets/{persona_name}.png")
        description = data.get('generated_description', data.get('original_description', ""))
        system_prompt = data.get('system_prompt', "")
        initial_message = data.get('initial_message', "")
        tags = data.get('tags', "")
        
        # We need to make sure the category is included if we want to support it later, 
        # but the current schema for friend_templates doesn't have a category column.
        # It has tags which often contains the category information.
        
        insert_stmt = (
            f"INSERT INTO friend_templates (name, avatar, description, system_prompt, initial_message, tags, created_at, updated_at) "
            f"VALUES ("
            f"{quote_sql(persona_name)}, "
            f"{quote_sql(avatar)}, "
            f"{quote_sql(description)}, "
            f"{quote_sql(system_prompt)}, "
            f"{quote_sql(initial_message)}, "
            f"{quote_sql(tags)}, "
            f"DATETIME('now'), "
            f"DATETIME('now')"
            f");"
        )
        sql_lines.append(insert_stmt)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))

    print(f"Successfully generated {len(personas)} INSERT statements in {output_path}")

if __name__ == "__main__":
    generate_sql()
