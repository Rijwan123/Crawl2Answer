const API_URL = "http://127.0.0.1:8000";


export async function crawlWebsite(url) {

  const response = await fetch(`${API_URL}/crawl`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json"
    },

    body: JSON.stringify({
      url: url
    })
  });


  const data = await response.json();


  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to crawl website"
    );
  }


  return data;
}


export async function askQuestion(question) {

  const response = await fetch(`${API_URL}/ask`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json"
    },

    body: JSON.stringify({
      question: question
    })
  });


  const data = await response.json();


  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to get answer"
    );
  }


  return data;
}