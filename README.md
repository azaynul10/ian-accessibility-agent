# IAN: Intelligent Accessibility Navigator

![Retro Tech Robot GIF](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZWM0YjI5ZDAyOWRiZTY4YTEyNDRlODMyZTM4NDk1YTZiYjY4YjMzYSZlcD12MV9pbnRlcm5hbF9naWZzX3NlYXJjaCZjdD1n/IZY2SE2JmPgFG/giphy.gif)

**⚠️ GEMINI LIVE AGENT CHALLENGE 2026 SUBMISSION ⚠️**

Voice-driven, autonomous web navigation powered by Gemini 2.5 Native Audio & Vision.

## Welcome
Welcome to the official repository for IAN! 👋

Navigating the modern web can be an absolute nightmare for visually impaired users. Traditional screen readers break the moment they hit a messy DOM or a cluttered e-commerce site. IAN fixes this by bypassing the code entirely. You speak naturally to our Neo-brutalist React dashboard, and IAN physically "sees" the screen and clicks through the browser for you using headless Chromium.

Built with blood, sweat, and Google Cloud credits for the Google Gemini Live Agent Challenge.

## Watch the Live Demo
[![Watch the IAN Demo](https://img.youtube.com/vi/dLxiK394WOc/maxresdefault.jpg)](https://www.youtube.com/watch?v=dLxiK394WOc&t=54s)

*Click the image above to watch the agent navigate Amazon autonomously!*

## Dual-Model Architecture
To prevent API rate limits and avoid blocking the WebSocket event loop, IAN splits the brain into two separate processes using the Google Agent Development Kit (ADK):

- **The Audio Orchestrator**: Streams live PCM audio to gemini-2.5-flash-native-audio to detect voice commands and extract the user's intent with zero-shot accuracy.
- **The Visual Navigator**: A background thread running headless Playwright that uses gemini-2.5-flash to analyze browser screenshots and calculate precise (X, Y) coordinates to click and type.

### Architecture Diagram
Since the original image link is broken or inaccessible, here's a text-based representation of the architecture using Mermaid for better rendering on GitHub:

```mermaid
graph TD
    A[User Voice Input] --> B[Audio Orchestrator]
    B --> C[Gemini 2.5 Flash Native Audio]
    C --> D[Intent Extraction]
    D --> E[WebSocket Event Loop]
    E --> F[Visual Navigator]
    F --> G[Headless Playwright Chromium]
    G --> H[Browser Screenshot]
    H --> I[Gemini 2.5 Flash Vision Analysis]
    I --> J["Calculate (X, Y) Coordinates"]
    J --> K[Click/Type Actions]
    K --> G
    subgraph "Google Agent Development Kit (ADK)"
        B
        F
    end
    L[Google Cloud Run] -.-> F
```

This diagram illustrates the flow from user input through audio processing, intent extraction, and visual navigation in a looped browser interaction. If you have the original diagram details, it can be refined further.

## Currently Working On

| Optimization Focus | Details |
|--------------------|---------|
| **🛠️ Optimizing the Agent** <br> Right now, the focus is strictly on stability and hackathon delivery! <br> <ul><li>✅ Finalizing the <strong>Dual-Model Architecture</strong> to prevent API rate limits.</li><li>✅ Perfecting the <strong>AG-UI WebSocket Protocol</strong> for real-time Voice Activity Detection.</li><li>🔄 Scaling the Playwright visual agent loop on <strong>Google Cloud Run</strong>.</li><li>🔜 Adding support for multi-tab contextual memory.</li></ul> <br> [👉 <strong>Vote for us on Devpost!</strong>](https://devpost.com/) | ![Hacking GIF](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMW5kOHg4b2UyZ2R5cGVxYXZ1bzJtcWVxdnZ6MjI0NmQ2ZjM1eTB2NyZlcD12MV9pbnRlcm5hbF9naWZzX3NlYXJjaCZjdD1n/L1R1tvI9svkIWwpVYr/giphy.gif) |

## Tech Stack & Skills
Built with a thread-safe, non-blocking Python/React stack.

### The Brains
- Gemini 2.5 Flash (Native Audio & Vision)
- Google Agent Development Kit (ADK)

### The Brawn (Backend)
- Python
- Playwright for headless Chromium
- Google Cloud Run

### The Beauty (Frontend)
- React (Neo-brutalist dashboard)
- WebSocket for real-time communication

## Establish Connection
Built by Zaynul Abedin Miah – Tech Community Leader & AI Developer.

Let's collaborate, talk about AGI, or build something awesome together!

## Establish Connection
Built by Zaynul Abedin Miah – Tech Community Leader & AI Developer.

Let's collaborate, talk about AGI, or build something awesome together!

[![Twitter](https://img.shields.io/badge/X%20(Twitter)-000000?style=for-the-badge&logo=x&logoColor=ffffff)](https://x.com/azaynul123)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-000000?style=for-the-badge&logo=linkedin&logoColor=00ffcc)](https://www.linkedin.com/in/zaynul-abedin-miah/)
[![Facebook](https://img.shields.io/badge/Facebook-000000?style=for-the-badge&logo=facebook&logoColor=ccff00)](https://www.facebook.com/azaynul123)

*"Stop parsing the DOM. Just look at the screen."*

*"Stop parsing the DOM. Just look at the screen."*
