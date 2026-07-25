# 🧩 Guardian A.N.Y — Frontend

> **Guardian A.N.Y.** (*Autista No YouTube*) — Interface web intuitiva e acessível criada para permitir a análise de vídeos do YouTube em tempo real, informando o nível de estímulo do conteúdo.

---

## 📌 Visão Geral

O frontend do **Guardian A.N.Y.** foi projetado para ser leve, rápido e simples de usar:
* **Entrada Acessível**: Permite colar links do YouTube (padrão ou encurtados `youtu.be`).
* **Feedback Visual**: Exibe o título do vídeo, a classificação gerada pela IA e os indicadores de estimulação de forma clara.
* **Comunicação em Tempo Real**: Consome a API do backend via requisições assíncronas.

---

## 🛠️ Tecnologias Utilizadas

* **HTML5 / CSS3**
* **Tailwind CSS**: Estilização moderna e responsiva.
* **JavaScript (Vanilla JS / ES6+)**: Lógica de integração e manipulação do DOM sem sobrecarga de frameworks.

---

## 🚀 Como Executar Localmente

Como o projeto é estático no frontend, você não precisa de um ambiente complexo:

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/leticiabeatriz15/Guardian-A.N.Y---Frontend.git](https://github.com/leticiabeatriz15/Guardian-A.N.Y---Frontend.git)
   cd Guardian-A.N.Y---Frontend

```

2. **Configuração da API:**
Abra o arquivo `script.js` e verifique a URL base da API:
* Para desenvolvimento local: `http://localhost:8000`
* Para produção: `https://guardian-a-n-y-backend.onrender.com`


3. **Execução:**
Abra o arquivo `index.html` diretamente no seu navegador ou utilize a extensão **Live Server** do VS Code.

---

## ☁️ Deploy

O frontend é hospedado na **Vercel**, garantindo entrega rápida e integração contínua a cada commit no repositório.