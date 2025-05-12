# Gerador de Frases em Inglês para Anki

Uma aplicação web simples para gerar frases de exemplo em inglês e criar flashcards para o Anki.

## Funcionalidades

- Geração de 10 frases de exemplo para qualquer palavra, phrasal verb ou expressão em inglês
- Frases naturais em contextos diversos (informal, negócios, viagens, acadêmico, etc.)
- Geração automática de um arquivo .apkg para importação direta no Anki
- Interface responsiva que funciona em dispositivos móveis e desktop

## Requisitos

- Python 3.6 ou superior
- Flask
- Requests
- Genanki
- Python-dotenv

## Configuração de Segurança

### Configuração Local

1. Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:
   ```
   GROQ_API_KEY=sua_chave_api_groq_aqui
   ```

2. Substitua `sua_chave_api_groq_aqui` com sua chave API Groq real.

3. Certifique-se que o arquivo `.env` está no `.gitignore` para não ser enviado ao GitHub.

### Configuração no Vercel

Se o aplicativo estiver hospedado na Vercel, adicione a variável de ambiente:

1. No painel da Vercel, acesse seu projeto
2. Vá para "Settings" → "Environment Variables"
3. Adicione uma nova variável chamada `GROQ_API_KEY` com sua chave API como valor
4. Clique em "Save" para salvar as alterações

### Nota sobre a API GROQ

Este aplicativo utiliza a API GROQ para gerar frases de exemplo em inglês e suas traduções em português brasileiro. É importante manter a chave API atualizada tanto no ambiente local quanto no ambiente de produção para garantir o correto funcionamento da aplicação.

### Segurança da Chave API

- Nunca compartilhe sua chave API ou a adicione diretamente no código-fonte
- Rotacione periodicamente sua chave API para maior segurança
- Se suspeitar que sua chave foi comprometida, revogue-a e gere uma nova

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/anki-generate.git
cd anki-generate
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Configure o arquivo `.env` com sua chave API GROQ conforme descrito acima

4. Execute a aplicação:
```
python app.py
```

5. Acesse a aplicação no navegador em `http://localhost:5000`

## Como usar

1. Digite uma palavra ou expressão em inglês no campo de entrada
2. Clique em "Gerar Frases" 
3. Visualize as 10 frases de exemplo geradas
4. Clique em "Baixar Deck Anki" para criar e baixar o arquivo .apkg
5. Importe o arquivo .apkg no Anki

## Tecnologias utilizadas

- Backend: Python/Flask
- Frontend: HTML/CSS/JavaScript
- API: GROQ
- Anki: Genanki (biblioteca Python)

## Licença

MIT 


### Nota sobre a API GROQ

Este aplicativo utiliza a API GROQ para gerar frases de exemplo em ingl�s e suas tradu��es em portugu�s brasileiro. � importante manter a chave API atualizada tanto no ambiente local quanto no ambiente de produ��o para garantir o correto funcionamento da aplica��o.
