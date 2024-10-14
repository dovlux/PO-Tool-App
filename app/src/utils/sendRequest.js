const sendRequest = async (
  url, payload = null, type = 'GET',
) => {
  const options = {
    method: type,
  };

  if (payload) {
    options.headers = { 'Content-Type': 'application/json' };
    options.body = JSON.stringify(payload);
  }

  let requestUrl = `http://127.0.0.1:8000/api/${url}`;

  const response = await fetch(requestUrl, options);

  let data = await response.json();

  if (!response.ok) {
    console.log(`Error! Message: ${data.detail}`);
    throw new Error(data.detail);
  }

  return data;
}

export default sendRequest;