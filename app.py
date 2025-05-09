import os
import json
import uuid
import tempfile
import requests
import random
import re
import csv
from flask import Flask, render_template, request, jsonify, send_file, url_for
from dotenv import load_dotenv
import genanki

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__, static_folder='static')
# Obter a chave API do ambiente
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

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
    use_natural_language = data.get('use_natural_language', False)
    
    if not input_text:
        return jsonify({'error': 'Texto não pode ser vazio'}), 400
    
    # Prompt base
    prompt_base = f"""Create 10 natural-sounding example sentences using the word or phrase "{input_text}" in diverse contexts. 
Ensure all sentences are grammatically correct and sound like they were written by native English speakers.
Use varied sentence structures, tenses, and common collocations with "{input_text}"."""

    # Adicionar instruções específicas para linguagem natural se a opção estiver ativada
    if use_natural_language:
        prompt_natural = f"""
Make the sentences sound conversational and informal, as used in everyday situations.
Include some common slang, idioms, and casual expressions where appropriate.
The sentences should reflect how native speakers actually talk in real-life situations.
Focus on contexts like casual conversations between friends, informal emails, text messages, or social media posts.
"""
        prompt_base += prompt_natural
    else:
        prompt_formal = f"""
Keep the sentences more formal and standard, suitable for academic or professional contexts.
Focus on clear, straightforward usage examples that demonstrate proper grammar.
"""
        prompt_base += prompt_formal

    # Continuar com o restante do prompt
    prompt = prompt_base + f"""
For each English sentence, provide a natural-sounding Brazilian Portuguese translation (not European Portuguese).
Focus on natural translations that capture the meaning and context, not just word-for-word translations.

Pay special attention to idiomatic expressions, phrasal verbs, and slang:
- "hang out" should be translated contextually as "sair", "curtir", "se encontrar", "passar tempo juntos", or "relaxar" depending on context
- "hitchhike" should be "pedir carona" (not "pé-fogo")
- "awesome" should be "incrível" or "sensacional" (not "fixe")
- "take on" should be "assumir" or "enfrentar" (depending on context)

Always translate the entire sentence as a whole, considering its complete meaning, rather than just replacing individual expressions.

Output as JSON array in this format:
[
  {{
    "english": "Example sentence in English using {input_text}",
    "portuguese": "Tradução natural da frase em português do Brasil"
  }},
  ... (9 more examples)
]

Make translations sound natural to Brazilians, as if they were originally written in Portuguese."""

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
    """Tradução contextual de frases em inglês para português brasileiro"""
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
        
        # Expressões específicas com traduções contextuais
        "hang out": "sair",
        "hang out with friends": "sair com amigos",
        "want to hang out": "quer sair",
        "going to hang out": "vamos sair",
        "hang out at": "ficar em",
        "hang out at the beach": "passar um tempo na praia",
        "we can hang out": "podemos nos encontrar",
        "just want to hang out": "só quero relaxar",
        "hang out together": "passar um tempo juntos",
        "like to hang out": "gosto de passar tempo",
        
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
        
        # Expressões contextuais para hang out
        "We're going to hang out at the beach": "Vamos curtir a praia",
        "I'm free on Friday, want to hang out": "Estou livre na sexta, quer sair comigo",
        "After the concert, we can hang out": "Depois do show, podemos conversar/bater papo",
        "I'm not really feeling like working today, just want to hang out": "Não estou muito motivado para trabalhar hoje, só quero relaxar"
    }
    
    # Primeiro tentar frases completas para contexto
    for phrase, translation in sorted(translations.items(), key=lambda x: len(x[0]), reverse=True):
        if phrase in text:
            text = text.replace(phrase, translation)
    
    # Depois tentar palavras individuais que possam ter restado
    for word, trans in sorted([(k, v) for k, v in translations.items() if ' ' not in k], key=lambda x: len(x[0]), reverse=True):
        if word in text:
            text = text.replace(word, trans)
    
    return text

# Adicionar exemplos específicos para "hang out"
def get_hang_out_examples():
    """Exemplos específicos para 'hang out' com traduções corretas e contextuais"""
    english_sentences = [
        "We're going to <span class=\"keyword\">hang out</span> at the beach this weekend.",
        "I'm free on Friday, want to <span class=\"keyword\">hang out</span> and grab dinner?",
        "After the concert, we can <span class=\"keyword\">hang out</span> and talk about the music.",
        "I'm not really feeling like working today, just want to <span class=\"keyword\">hang out</span>.",
        "Let's <span class=\"keyword\">hang out</span> at my place and watch some movies.",
        "She likes to <span class=\"keyword\">hang out</span> with her colleagues after work.",
        "Where do the young people <span class=\"keyword\">hang out</span> in this town?",
        "We used to <span class=\"keyword\">hang out</span> at the park when we were kids.",
        "I need a place to <span class=\"keyword\">hang out</span> and relax for a few hours.",
        "My friends and I <span class=\"keyword\">hang out</span> online playing video games."
    ]
    
    portuguese_sentences = [
        "Vamos curtir a praia neste fim de semana.",
        "Estou livre na sexta, quer sair e jantar?",
        "Depois do show, podemos bater um papo sobre a música.",
        "Não estou muito a fim de trabalhar hoje, só quero relaxar.",
        "Vamos ficar lá em casa e assistir alguns filmes.",
        "Ela gosta de sair com os colegas de trabalho depois do expediente.",
        "Onde os jovens costumam se reunir nesta cidade?",
        "Costumávamos nos encontrar no parque quando éramos crianças.",
        "Preciso de um lugar para passar o tempo e relaxar por algumas horas.",
        "Meus amigos e eu nos reunimos online para jogar videogames."
    ]
    
    sentences = []
    for i, english in enumerate(english_sentences):
        sentences.append({
            "english": english,
            "portuguese": portuguese_sentences[i]
        })
    
    return sentences

# Função para gerar frases de exemplo como fallback
def get_fallback_sentences(input_text):
    """Gera frases de exemplo com traduções em português brasileiro para o fallback"""
    
    # Casos especiais para expressões muito usadas
    if input_text.lower() == "hang out":
        return get_hang_out_examples()
    
    # Determinar o tipo de entrada para gerar exemplos mais apropriados
    is_phrasal_verb = ' ' in input_text.strip()
    
    if is_phrasal_verb:
        # Exemplos para phrasal verbs
        if input_text == "give up":
            english_sentences = [
                f"After months of trying, she finally gave up smoking for good.",
                f"Don't give up on your dreams just because of one setback.",
                f"He gave up his seat to an elderly woman on the bus.",
                f"The team refused to give up despite being down by ten points.",
                f"I'm not going to give up until I find the perfect solution.",
                f"Many students give up learning a language when it gets difficult.",
                f"They decided to give up their apartment and travel the world instead.",
                f"Sometimes you have to give up certain luxuries to save money.",
                f"The CEO gave up his bonus so the employees could get raises.",
                f"We'll never give up looking for answers to these questions."
            ]
            portuguese_sentences = [
                "Depois de meses tentando, ela finalmente desistiu de fumar de vez.",
                "Não desista dos seus sonhos só por causa de um contratempo.",
                "Ele cedeu seu lugar para uma senhora idosa no ônibus.",
                "O time se recusou a desistir apesar de estar perdendo por dez pontos.",
                "Não vou desistir até encontrar a solução perfeita.",
                "Muitos estudantes desistem de aprender um idioma quando fica difícil.",
                "Eles decidiram abrir mão do apartamento e viajar pelo mundo.",
                "Às vezes você precisa abrir mão de certos luxos para economizar dinheiro.",
                "O CEO abriu mão de seu bônus para que os funcionários pudessem receber aumentos.",
                "Nunca desistiremos de procurar respostas para essas questões."
            ]
        elif input_text == "take on":
            english_sentences = [
                f"She decided to take on the challenge of running a marathon.",
                f"Our company will take on five new employees this month.",
                f"He shouldn't take on more responsibilities right now.",
                f"The team took on last year's champions in the final game.",
                f"I can't take on any more work this week.",
                f"They took on the project despite the tight deadline.",
                f"The new CEO plans to take on the competition aggressively.",
                f"She's going to take on a new role at the company.",
                f"Don't take on too much debt while you're still studying.",
                f"The small firm took on a multinational corporation in court."
            ]
            portuguese_sentences = [
                "Ela decidiu assumir o desafio de correr uma maratona.",
                "Nossa empresa vai contratar cinco novos funcionários este mês.",
                "Ele não deveria assumir mais responsabilidades agora.",
                "O time enfrentou os campeões do ano passado no jogo final.",
                "Não posso assumir mais trabalho esta semana.",
                "Eles assumiram o projeto apesar do prazo apertado.",
                "O novo CEO planeja enfrentar a concorrência de forma agressiva.",
                "Ela vai assumir uma nova função na empresa.",
                "Não assuma muitas dívidas enquanto ainda estiver estudando.",
                "A pequena empresa enfrentou uma multinacional na justiça."
            ]
        else:
            # Exemplos genéricos para outros phrasal verbs
            english_sentences = [
                f"I really need to {input_text} more often to improve my skills.",
                f"She decided to {input_text} her project before the deadline.",
                f"Don't {input_text} until you've considered all options.",
                f"They {input_text} together very well as a team.",
                f"You should never {input_text} when facing difficulties.",
                f"The team plans to {input_text} during the next competition.",
                f"He had to {input_text} his schedule to make time for family.",
                f"I'll {input_text} whenever I have the opportunity.",
                f"Sometimes you have to {input_text} to achieve your goals.",
                f"The company will {input_text} new initiatives next year."
            ]
            # Traduzir usando a função existente
            portuguese_sentences = [translate_to_portuguese(sentence) for sentence in english_sentences]
    else:
        # Exemplos para palavras individuais - adaptados pela função de input
        if input_text in ["amazing", "awesome", "incredible", "fantastic"]:
            # Adjetivos positivos
            english_sentences = [
                f"That was an {input_text} concert last night.",
                f"She gave an {input_text} performance in the play.",
                f"The view from the top of the mountain is truly {input_text}.",
                f"It's {input_text} how quickly children learn new languages.",
                f"Thank you for the {input_text} dinner you prepared.",
                f"They did an {input_text} job on the renovation.",
                f"The new restaurant downtown has {input_text} food.",
                f"You look {input_text} in that new outfit!",
                f"The team made an {input_text} comeback in the second half.",
                f"It was {input_text} to see everyone together again after so long."
            ]
            portuguese_translations = {
                "amazing": "incrível",
                "awesome": "sensacional",
                "incredible": "inacreditável",
                "fantastic": "fantástico"
            }
            translate_word = portuguese_translations.get(input_text.lower(), "incrível")
            portuguese_sentences = [
                f"Foi um show {translate_word} ontem à noite.",
                f"Ela fez uma apresentação {translate_word} na peça.",
                f"A vista do topo da montanha é realmente {translate_word}.",
                f"É {translate_word} como as crianças aprendem novos idiomas rapidamente.",
                f"Obrigado pelo jantar {translate_word} que você preparou.",
                f"Eles fizeram um trabalho {translate_word} na reforma.",
                f"O novo restaurante no centro tem uma comida {translate_word}.",
                f"Você está {translate_word} nessa roupa nova!",
                f"O time fez uma recuperação {translate_word} no segundo tempo.",
                f"Foi {translate_word} ver todos juntos novamente depois de tanto tempo."
            ]
        else:
            # Exemplos genéricos para outras palavras
            english_sentences = [
                f"The {input_text} was much better than I expected.",
                f"She has an impressive {input_text} that many people admire.",
                f"We should {input_text} more carefully in this situation.",
                f"His {input_text} impressed everyone at the conference.",
                f"I've never seen such a remarkable {input_text} before.",
                f"Can you {input_text} this more effectively, please?",
                f"The {input_text} in this region is quite unique.",
                f"She likes to {input_text} regularly with her colleagues.",
                f"My instructor taught me how to {input_text} correctly.",
                f"This {input_text} reminds me of my childhood experiences."
            ]
            # Traduzir usando a função existente
            portuguese_sentences = [translate_to_portuguese(sentence) for sentence in english_sentences]
    
    sentences = []
    for i, english in enumerate(english_sentences):
        highlighted = highlight_keyword(english, input_text)
        portuguese = portuguese_sentences[i] if i < len(portuguese_sentences) else translate_to_portuguese(english)
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
    format_type = data.get('format', 'apkg')  # Nova opção: apkg ou csv
    
    try:
        if format_type == 'csv':
            # Criar arquivo CSV para importação em um deck existente
            temp_dir = tempfile.mkdtemp()
            csv_path = os.path.join(temp_dir, f'english_sentences_{word}.csv')
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                # Escrever cabeçalho que o Anki reconhece
                csvwriter.writerow(['front', 'back'])
                
                # Adicionar as frases
                for sentence in sentences:
                    if "english" in sentence and "portuguese" in sentence:
                        english = sentence["english"]
                        portuguese = sentence["portuguese"]
                    else:
                        english = sentence.get("back", "")
                        portuguese = sentence.get("translation", "")
                    
                    csvwriter.writerow([english, portuguese])
            
            return send_file(csv_path, as_attachment=True, download_name=f'english_sentences_{word}.csv')
        else:
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
        print(f"Erro ao criar arquivo: {str(e)}")
        return jsonify({'error': f'Erro ao criar arquivo: {str(e)}'}), 500

# Adicionar handler para o servidor WSGI
app.debug = False

# Exportar app para Vercel
if __name__ == '__main__':
    app.run(debug=True)
else:
    # Para o Vercel - importante que a variável se chame 'app'
    app = app 