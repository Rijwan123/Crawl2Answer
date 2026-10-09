import { useState } from "react";
import { crawlWebsite, askQuestion } from "./api";
import "./App.css";

function App() {
  const [url, setUrl] = useState("");
  const [question, setQuestion] = useState("");

  const [crawlMessage, setCrawlMessage] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);

  const [crawling, setCrawling] = useState(false);
  const [asking, setAsking] = useState(false);
  const [indexed, setIndexed] = useState(false);

  const [pages, setPages] = useState(0);
  const [chunks, setChunks] = useState(0);

  async function handleCrawl() {
    if (!url.trim()) {
      setCrawlMessage("Please enter a website URL.");
      return;
    }

    try {
      setCrawling(true);
      setIndexed(false);
      setAnswer("");
      setSources([]);

      setCrawlMessage("Crawling and indexing website...");

      const data = await crawlWebsite(url);

      setPages(data.pages || 0);
      setChunks(data.chunks || 0);

      setCrawlMessage("Website indexed successfully.");
      setIndexed(true);
    } catch (error) {
      setCrawlMessage(error.message);
    } finally {
      setCrawling(false);
    }
  }

  async function handleAsk() {
    if (!question.trim()) return;

    try {
      setAsking(true);
      setAnswer("");
      setSources([]);

      const data = await askQuestion(question);

      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (error) {
      setAnswer(error.message);
    } finally {
      setAsking(false);
    }
  }

  function clearAnswer() {
    setQuestion("");
    setAnswer("");
    setSources([]);
  }

  return (
    <div className="app">
      <div className="background-orb orb-one"></div>
      <div className="background-orb orb-two"></div>

      <main className="container">
        {/* Header */}
        <header className="hero">
          <div className="hero-top">
            <div className="brand-icon">AI</div>

            <div className="status-pill">
              <span className="status-dot"></span>
              Backend connected
            </div>
          </div>
          <h1>Website RAG Assistant</h1>
          <br></br>
          <br></br>
          <p>
            Crawl any website, build a searchable knowledge base,
            and ask questions using AI.
          </p>
        </header>

        {/* Crawl card */}
        <section className="card">
          <div className="card-header">

            <div className="step-number">
              01
            </div>

            <div className="card-title-group">

              <h2>
                Index a website
              </h2>

              <p>
                Enter a public website URL to crawl and prepare its
                content for retrieval.
              </p>

            </div>

          </div>

          <div className="url-row">
            <div className="input-wrapper">
              <span className="input-icon">🌐</span>

              <input
                type="url"
                placeholder="https://docs.example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>

            <button
              className="primary-button"
              onClick={handleCrawl}
              disabled={crawling}
            >
              {crawling ? (
                <>
                  <span className="spinner"></span>
                  Crawling...
                </>
              ) : (
                "Crawl Website"
              )}
            </button>
          </div>

          {crawlMessage && (
            <div
              className={`crawl-status ${
                indexed ? "success" : ""
              }`}
            >
              <div>
                <strong>{crawlMessage}</strong>

                {indexed && (
                  <span>
                    {pages} page(s) crawled • {chunks} chunks indexed
                  </span>
                )}
              </div>
            </div>
          )}
        </section>

        {/* Ask card */}
        <section className="card">
          <div className="card-header">

            <div className="step-number">
              02
            </div>

            <div className="card-title-group">

              <h2>
                Ask your knowledge base
              </h2>

              <p>
                Ask questions based only on the indexed website content.
              </p>

            </div>

          </div>

          <div className="question-box">
            <textarea
              placeholder={
                indexed
                  ? "Example: How do I create an agent using LangChain?"
                  : "Index a website first to start asking questions..."
              }
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={!indexed}
            />

            <div className="question-actions">
              <span className="helper-text">
                {indexed
                  ? "AI will answer using retrieved website context."
                  : "Waiting for website indexing."}
              </span>

              <button
                className="primary-button ask-button"
                onClick={handleAsk}
                disabled={!indexed || asking || !question.trim()}
              >
                {asking ? (
                  <>
                    <span className="spinner"></span>
                    Thinking...
                  </>
                ) : (
                  "Ask AI"
                )}
              </button>
            </div>
          </div>
        </section>

        {/* Answer card */}
        {(answer || asking) && (
          <section className="answer-card">
            <div className="answer-header">
              <div>
                <span className="answer-label">AI RESPONSE</span>
                <h2>Answer</h2>
              </div>

              <button
                className="clear-button"
                onClick={clearAnswer}
              >
                Clear
              </button>
            </div>

            {asking ? (
              <div className="thinking-state">
                <span className="spinner large"></span>

                <div>
                  <strong>Searching indexed content</strong>
                  <p>Retrieving the most relevant chunks...</p>
                </div>
              </div>
            ) : (
              <>
                <div className="answer-content">
                  {answer}
                </div>

                {sources.length > 0 && (
                  <div className="sources-section">
                    <h3>Sources</h3>

                    <div className="source-list">
                      {sources.map((source, index) => (
                        <a
                          key={index}
                          href={source}
                          target="_blank"
                          rel="noreferrer"
                          className="source-card"
                        >
                          <div className="source-number">
                            {index + 1}
                          </div>

                          <div className="source-details">
                            <span>Referenced source</span>
                            <p>{source}</p>
                          </div>

                          <span className="external-icon">
                            ↗
                          </span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </section>
        )}

        <footer>
          Built with FastAPI • LangChain • Apify • OpenAI • React
        </footer>
      </main>
    </div>
  );
}

export default App;