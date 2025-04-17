import os
import json
import uuid
import tempfile
import requests
import random
import re
from flask import Flask, render_template, request, jsonify, send_file, url_for
from dotenv import load_dotenv
import genanki

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__, static_folder='static')
# Definir a chave API diretamente
GROQ_API_KEY = "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"

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    input_text = data.get('input_text', '')
    
    if not input_text:
        return jsonify({'error': 'Texto não pode ser vazio'}), 400
    
    # Prompt para gerar frases em inglês com tradução em português
    prompt = f"""Create 10 example sentences using the word or phrase "{input_text}" in different contexts. 
For each English sentence, provide a Brazilian Portuguese translation (not European Portuguese).
Note: Use Brazilian Portuguese vocabulary and expressions. For example, "hitchhike" should be "pedir carona" (not "pé-fogo").

Output as JSON array in this format:
[
  {{
    "english": "Example sentence in English using {input_text}",
    "portuguese": "Tradução da frase em português do Brasil"
  }},
  ... (9 more examples)
]
Make translations natural and accurate for Brazilian Portuguese speakers."""

    try:
        # Chamada para a API GROQ
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        
        if response.status_code != 200:
            error_message = f"Erro na API GROQ (Status {response.status_code}): {response.text}"
            print(error_message)
            return jsonify({'error': error_message}), 500
        
        try:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Método simplificado para extrair JSON
            try:
                # Tentar encontrar o JSON no texto
                start = content.find('[')
                end = content.rfind(']') + 1
                
                if start >= 0 and end > start:
                    json_content = content[start:end]
                    sentences_raw = json.loads(json_content)
                    
                    # Converter formato ou criar frases de exemplo com traduções
                    if not sentences_raw or not isinstance(sentences_raw, list):
                        sentences = get_fallback_sentences(input_text)
                    else:
                        sentences = []
                        for item in sentences_raw:
                            # Verifica o formato e adapta se necessário
                            if "english" in item and "portuguese" in item:
                                # Destacar a palavra-chave
                                item["english"] = highlight_keyword(item["english"], input_text)
                                sentences.append(item)
                            elif "back" in item and "translation" in item:
                                english = highlight_keyword(item["back"], input_text)
                                sentences.append({
                                    "english": english,
                                    "portuguese": item["translation"]
                                })
                            elif "front" in item and "back" in item:
                                portuguese = item.get("translation", translate_to_portuguese(item["back"]))
                                english = highlight_keyword(item["back"], input_text)
                                sentences.append({
                                    "english": english,
                                    "portuguese": portuguese
                                })
                    
                    return jsonify({'sentences': sentences, 'keyword': input_text})
                else:
                    # Fallback para frases de exemplo se não encontrar JSON
                    raise ValueError("Não foi possível encontrar JSON válido na resposta")
                    
            except Exception as json_error:
                print(f"Erro ao analisar JSON: {str(json_error)}")
                print(f"Conteúdo recebido: {content[:500]}")
                
                # Criar frases de exemplo como fallback com traduções
                sentences = get_fallback_sentences(input_text)
                return jsonify({'sentences': sentences, 'keyword': input_text})
                
        except Exception as parse_error:
            print(f"Erro ao processar resposta: {str(parse_error)}")
            print(f"Resposta bruta: {response.text[:500]}")
            return jsonify({'error': f'Erro ao processar resposta: {str(parse_error)}'}), 500
    
    except Exception as request_error:
        print(f"Erro ao fazer requisição: {str(request_error)}")
        return jsonify({'error': f'Erro ao conectar com a API: {str(request_error)}'}), 500

# Função para destacar a palavra-chave no texto
def highlight_keyword(text, keyword):
    """Destaca a palavra-chave com HTML para negrito e cor"""
    # Regex para encontrar a palavra-chave preservando maiúsculas/minúsculas
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    
    # Substituir a palavra-chave pelo HTML destacado
    highlighted = pattern.sub(r'<span class="keyword">\g<0></span>', text)
    return highlighted

# Função para traduzir texto para português como fallback
def translate_to_portuguese(text):
    """Tradução básica de frases simples em inglês para português brasileiro"""
    translations = {
        # Verbos e expressões comuns
        "I need to": "Eu preciso",
        "She decided to": "Ela decidiu",
        "Don't": "Não",
        "They": "Eles",
        "You should never": "Você nunca deve",
        "The team refused to": "O time se recusou a",
        "He had to": "Ele teve que",
        "I'll never": "Eu nunca vou",
        "Sometimes you have to": "Às vezes você tem que",
        "The company will": "A empresa vai",
        
        # Substantivos e objetos
        "smoking": "fumar",
        "her job": "seu emprego",
        "dreams": "sonhos",
        "after trying for hours": "depois de tentar por horas",
        "when things get difficult": "quando as coisas ficam difíceis",
        "despite being behind": "apesar de estar perdendo",
        "his favorite hobby": "seu hobby favorito",
        "injury": "lesão",
        "trying to improve my English": "tentar melhorar meu inglês",
        "certain habits": "certos hábitos",
        "to move forward": "para seguir em frente",
        "the project": "o projeto",
        "if it's not profitable": "se não for lucrativo",
        
        # Phrasal verbs e expressões idiomáticas
        "hitchhike": "pedir carona",
        "give up": "desistir",
        "take on": "assumir",
        "break down": "quebrar",
        "look up": "procurar",
        "turn in": "entregar",
        "get along": "se dar bem",
        "put off": "adiar",
        "figure out": "descobrir",
        "run into": "encontrar por acaso",
        "show off": "se exibir",
        "work out": "resolver",
        "set up": "configurar",
        "hang out": "passar tempo",
        "speak up": "falar mais alto",
        "cheer up": "animar",
        "get over": "superar",
        "go over": "revisar",
        "pick up": "pegar",
        "in a nutshell": "em resumo",
        "piece of cake": "moleza",
        "once in a blue moon": "de vez em quando",
        "break a leg": "boa sorte",
        "kill two birds with one stone": "matar dois coelhos com uma cajadada só",
        "hit the nail on the head": "acertar na mosca",
        "bite the bullet": "encarar a situação",
        "on the same page": "na mesma sintonia",
        "under the weather": "indisposto",
        "cost an arm and a leg": "custar os olhos da cara",
        "cut corners": "economizar esforços",
        "call it a day": "dar o dia por encerrado",
        "let the cat out of the bag": "contar um segredo",
        "it's not rocket science": "não é nenhum bicho de sete cabeças",
        "out of the blue": "do nada",
        "a blessing in disguise": "um mal que vem para bem",
        "beat around the bush": "enrolar",
        
        # Gírias e expressões regionais comuns
        "cool": "legal",
        "awesome": "incrível",
        "hang out": "dar um rolê",
        "buddy": "cara",
        "check out": "dar uma olhada",
        "rip-off": "roubada",
        "no big deal": "sem problemas",
        "hands down": "sem dúvida",
        "all set": "tudo pronto",
        "way to go": "mandou bem",
        "on the fence": "em cima do muro",
        "mind-blowing": "de cair o queixo",
        "sketchy": "suspeito",
        "what's up": "e aí",
    }
    
    translated = text
    for eng, port in translations.items():
        translated = translated.replace(eng, port)
    
    return translated

# Função para gerar frases de exemplo como fallback
def get_fallback_sentences(input_text):
    """Gera frases de exemplo com traduções em português brasileiro para o fallback"""
    
    # Determinar o tipo de entrada para gerar exemplos mais apropriados
    is_phrasal_verb = ' ' in input_text.strip()
    
    if is_phrasal_verb:
        # Exemplos para phrasal verbs
        english_sentences = [
            f"I need to {input_text} smoking for my health.",
            f"She decided to {input_text} her job and travel the world.",
            f"Don't {input_text} on your dreams so easily.",
            f"They {input_text} after trying for hours.",
            f"You should never {input_text} when things get difficult.",
            f"The team refused to {input_text} despite being behind.",
            f"He had to {input_text} his favorite hobby due to his injury.",
            f"I'll never {input_text} trying to improve my English.",
            f"Sometimes you have to {input_text} certain habits to move forward.",
            f"The company will {input_text} the project if it's not profitable."
        ]
    else:
        # Exemplos para palavras individuais
        english_sentences = [
            f"The {input_text} was much bigger than we expected.",
            f"She has a great {input_text} that helps her in difficult situations.",
            f"We need to {input_text} before the deadline tomorrow.",
            f"His {input_text} impressed everyone at the meeting.",
            f"I've never seen such a beautiful {input_text} before.",
            f"Can you {input_text} this for me, please?",
            f"The {input_text} in this city is very different from my hometown.",
            f"She likes to {input_text} on the weekends with her friends.",
            f"My teacher taught me how to {input_text} properly.",
            f"This {input_text} reminds me of my childhood."
        ]
    
    sentences = []
    for sentence in english_sentences:
        portuguese = translate_to_portuguese(sentence)
        highlighted = highlight_keyword(sentence, input_text)
        sentences.append({
            "english": highlighted,
            "portuguese": portuguese
        })
    
    return sentences

@app.route('/create-deck', methods=['POST'])
def create_deck():
    data = request.json
    sentences = data.get('sentences', [])
    word = data.get('word', 'vocabulary')
    
    try:
        # CSS personalizado para o modelo Anki com suporte para destacar a palavra-chave
        custom_css = """
        .card {
            font-family: Arial, sans-serif;
            font-size: 20px;
            text-align: left;
            color: black;
            background-color: white;
            line-height: 1.5;
            padding: 15px;
        }
        .keyword {
            font-weight: bold;
            color: #4a86e8;
        }
        """
        
        # Criar modelo de nota para cartões bidirecionais (Basic and Reversed)
        model_id = random.randrange(1 << 30, 1 << 31)
        model = genanki.Model(
            model_id,
            'Basic (and reversed card)',
            fields=[
                {'name': 'Front'},
                {'name': 'Back'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '{{Front}}',
                    'afmt': '{{FrontSide}}<hr id="answer">{{Back}}',
                },
                {
                    'name': 'Card 2',
                    'qfmt': '{{Back}}',
                    'afmt': '{{FrontSide}}<hr id="answer">{{Front}}',
                }
            ],
            css=custom_css
        )
        
        # Criar deck
        deck_id = random.randrange(1 << 30, 1 << 31)
        deck = genanki.Deck(deck_id, f'English Examples: {word}')
        
        # Adicionar notas ao deck com tamanho de fonte maior
        for sentence in sentences:
            # Extrai os campos de acordo com o formato
            if "english" in sentence and "portuguese" in sentence:
                english = sentence["english"]
                portuguese = sentence["portuguese"]
            else:
                english = sentence.get("back", "")
                portuguese = sentence.get("translation", "")
            
            note = genanki.Note(
                model=model,
                fields=[english, portuguese]
            )
            deck.add_note(note)
            
        # Criar arquivo temporário para o deck
        temp_dir = tempfile.mkdtemp()
        deck_path = os.path.join(temp_dir, f'english_examples_{word}.apkg')
        
        # Criar arquivo temporário para o deck
        genanki.Package(deck).write_to_file(deck_path)
        
        return send_file(deck_path, as_attachment=True)
    
    except Exception as e:
        print(f"Erro ao criar deck: {str(e)}")
        return jsonify({'error': f'Erro ao criar deck: {str(e)}'}), 500

# Adicionar handler para o servidor WSGI
app.debug = False

# Exportar app para Vercel
if __name__ == '__main__':
    app.run(debug=True)
else:
    # Para o Vercel - importante que a variável se chame 'app'
    app = app 