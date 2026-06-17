import { useState } from 'react';

export default function UploadForm({ onResult }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [kindleEmail, setKindleEmail] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const [destination, setDestination] = useState('download');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      setMessage('Please select a PDF file.');
      return;
    }

    setLoading(true);
    setMessage('Uploading...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('author', author);
    formData.append('kindle_email', kindleEmail);
    formData.append('sender_email', senderEmail);
    formData.append('destination', destination);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = 'Upload failed';
        try {
          const errorBody = await response.json();
          errorMessage = errorBody.detail || errorBody.error || errorMessage;
        } catch (jsonError) {
          errorMessage = response.statusText || errorMessage;
        }
        setMessage(errorMessage);
        onResult(null);
      } else {
        const data = await response.json();
        setMessage('Upload complete.');
        onResult(data);
      }
    } catch (error) {
      setMessage('Unable to reach backend.');
      onResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block mb-2 font-medium">PDF File</label>
        <input
          type="file"
          accept="application/pdf"
          onChange={(event) => setFile(event.target.files[0])}
          className="w-full border rounded-lg p-2"
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block mb-2 font-medium">Title</label>
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Optional title override"
            className="w-full border rounded-lg p-2"
          />
        </div>
        <div>
          <label className="block mb-2 font-medium">Author</label>
          <input
            type="text"
            value={author}
            onChange={(event) => setAuthor(event.target.value)}
            placeholder="Optional author override"
            className="w-full border rounded-lg p-2"
          />
        </div>
      </div>
      <div>
        <label className="block mb-2 font-medium">Destination</label>
        <select
          value={destination}
          onChange={(event) => setDestination(event.target.value)}
          className="w-full border rounded-lg p-2"
        >
          <option value="download">Download EPUB</option>
          <option value="kindle">Send to Kindle</option>
        </select>
      </div>
      {destination === 'kindle' && (
        <>
          <div>
            <label className="block mb-2 font-medium">Kindle Email</label>
            <input
              type="email"
              value={kindleEmail}
              onChange={(event) => setKindleEmail(event.target.value)}
              placeholder="yourname@kindle.com"
              className="w-full border rounded-lg p-2"
            />
          </div>
          <div>
            <label className="block mb-2 font-medium">Sender Email (must be approved by Kindle)</label>
            <input
              type="email"
              value={senderEmail}
              onChange={(event) => setSenderEmail(event.target.value)}
              placeholder="sender@example.com"
              className="w-full border rounded-lg p-2"
            />
            <p className="text-xs text-slate-500 mt-1">This address should be the sender approved in your Amazon Kindle account.</p>
          </div>
        </>
      )}
      <button
        type="submit"
        disabled={loading}
        className="inline-flex items-center justify-center rounded-full bg-slate-900 text-white px-5 py-3 text-sm font-semibold hover:bg-slate-700 disabled:opacity-50"
      >
        {loading ? 'Processing…' : 'Upload and Convert'}
      </button>
      {message && <p className="text-sm text-slate-600">{message}</p>}
    </form>
  );
}
