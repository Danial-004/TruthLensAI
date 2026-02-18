import React, { useState } from "react";
import {
  Upload,
  Image as ImageIcon,
  Type,
  Link as LinkIcon,
  Loader2,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Textarea } from "./ui/textarea";
import { Input } from "./ui/input";
import { useTranslation } from "../hooks/useTranslation";

export default function VerificationTabs() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("text");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [query, setQuery] = useState("");
  const [url, setUrl] = useState("");
  const [urlPreview, setUrlPreview] = useState(null);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showJson, setShowJson] = useState(false);

  const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  // ТҮЗЕТІЛДІ: Типтер алынып тасталды, енді қате шықпайды
  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
      setResult(null);
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      setFile(droppedFile);
      setPreview(URL.createObjectURL(droppedFile));
      setResult(null);
      setError(null);
    }
  };

  const handleDragOver = (e) => e.preventDefault();

  const handleUrlChange = (e) => {
    const value = e.target.value;
    setUrl(value);
    setResult(null);
    setError(null);
    if (value.match(/^https?:\/\/.*\.(jpeg|jpg|png|gif|webp)$/i)) {
      setUrlPreview(value);
    } else {
      setUrlPreview(null);
    }
  };

  // Вердиктті аудару функциясы
  const formatVerdict = (verdictString) => {
    if (!verdictString || typeof verdictString !== 'string') {
      return t('uncertain');
    }

    const lowerVerdict = verdictString.toLowerCase();

    if (lowerVerdict.includes("real") || lowerVerdict.includes("подлинное")) {
      return `✅ ${t('real')}`;
    } else if (lowerVerdict.includes("fake") || lowerVerdict.includes("фейк")) {
      return `❌ ${t('fake')}`;
    } else if (lowerVerdict.includes("controversial") || lowerVerdict.includes("спорное")) {
      return `⚠️ ${t('uncertain')}`;
    } else {
      return `🤔 ${t('uncertain')}`;
    }
  };

  const handleSubmit = async () => {
    setError(null);
    setResult(null);
    setLoading(true);
    console.log(`Отправка запроса на ${activeTab.toUpperCase()}`);

    try {
      let response;
      let endpoint = "";

      if (activeTab === "text" && query) {
        endpoint = "/analyze";
        response = await fetch(`${API_BASE}${endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: query }),
        });
      } else if (activeTab === "image" && file) {
        endpoint = "/analyze_image";
        const formData = new FormData();
        formData.append("file", file);
        formData.append("text", query || "Check image");
        response = await fetch(`${API_BASE}${endpoint}`, {
          method: "POST",
          body: formData,
        });
      } else if (activeTab === "url" && url) {
        endpoint = "/analyze_url";
        const body = { url: url, text: query || "Check URL" };
        response = await fetch(`${API_BASE}${endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      } else {
        throw new Error(t('errorOccurred'));
      }

      if (!response.ok) {
        let msg = `Error ${response.status}`;
        try {
          const errorData = await response.json();
          msg = errorData.detail || errorData.message || msg;
        } catch {
          const errorText = await response.text();
          msg = errorText || msg;
        }
        throw new Error(msg);
      }

      const responseText = await response.text();
      const data = responseText ? JSON.parse(responseText) : { message: "Empty response" };
      setResult(data);

    } catch (err) {
      console.error("❌ Ошибка:", err);
      // Тип тексеруін алып тастадық, жай ғана message қараймыз
      const errorMessage = err.message || t('errorOccurred');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const tabButtonStyle = (tabName) => {
    const isActive = activeTab === tabName;
    return `
      flex-1 py-3 text-sm font-medium transition-all duration-300
      flex items-center justify-center gap-2
      ${isActive
        ? "bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.5)]"
        : "text-slate-400 hover:text-white hover:bg-white/5"}
    `;
  };

  return (
    <div className="w-full bg-transparent text-gray-100">
      <Card className="w-full border-0 shadow-none bg-transparent">

        {/* 2. Табтар: Жартылай мөлдір фон */}
        <div className="flex justify-between border-b border-white/10 bg-slate-900/40 backdrop-blur-sm rounded-t-xl p-1">
          <button onClick={() => setActiveTab("text")} className={tabButtonStyle("text")}>
            <Type className="inline-block w-4 h-4 mr-2" />
            {t('tabText')}
          </button>
          <button onClick={() => setActiveTab("image")} className={tabButtonStyle("image")}>
            <ImageIcon className="inline-block w-4 h-4 mr-2" />
            {t('tabImage')}
          </button>
          <button onClick={() => setActiveTab("url")} className={tabButtonStyle("url")}>
            <LinkIcon className="inline-block w-4 h-4 mr-2" />
            {t('tabUrl')}
          </button>
        </div>

        <CardContent className="mt-6 space-y-4">
          {/* === TEXT TAB === */}
          {activeTab === "text" && (
            <div className="animate-in fade-in zoom-in duration-300">
              <Textarea
                placeholder={t('placeholderText')}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setResult(null);
                  setError(null);
                }}
                className="bg-slate-900/50 backdrop-blur-sm border border-white/10 text-gray-100 min-h-[150px] rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder:text-gray-500"
              />
              <Button
                onClick={handleSubmit}
                disabled={loading || !query}
                className="mt-4 w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold py-2 rounded-xl transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : t('checkBtn')}
              </Button>
            </div>
          )}

          {/* === IMAGE TAB === */}
          {activeTab === "image" && (
            <div className="space-y-4 animate-in fade-in zoom-in duration-300">
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => document.getElementById("fileInput").click()}
                className="flex flex-col items-center justify-center border-2 border-dashed border-white/20 rounded-xl p-6 cursor-pointer bg-slate-900/30 hover:bg-slate-900/50 hover:border-blue-500 transition-all backdrop-blur-sm"
              >
                {preview ? (
                  <img src={preview} alt="preview" className="max-h-56 rounded-lg object-contain shadow-lg" />
                ) : (
                  <div className="flex flex-col items-center text-gray-400">
                    <Upload className="w-10 h-10 mb-2 text-blue-400" />
                    <p className="text-sm text-center">{t('dragDrop')}</p>
                  </div>
                )}
                <input id="fileInput" type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
              </div>

              <Textarea
                placeholder={t('placeholderImageQuery')}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="bg-slate-900/50 backdrop-blur-sm border border-white/10 text-gray-100 min-h-[100px] rounded-xl focus:ring-2 focus:ring-blue-500 placeholder:text-gray-500"
              />

              <Button
                onClick={handleSubmit}
                disabled={!file || loading}
                className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold py-2 rounded-xl transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : t('checkBtn')}
              </Button>
            </div>
          )}

          {/* === URL TAB === */}
          {activeTab === "url" && (
            <div className="space-y-4 animate-in fade-in zoom-in duration-300">
              <Input
                type="url"
                placeholder={t('placeholderUrl')}
                value={url}
                onChange={handleUrlChange}
                className="bg-slate-900/50 backdrop-blur-sm border border-white/10 text-gray-100 placeholder-gray-500 rounded-xl focus:ring-2 focus:ring-blue-500 h-12"
              />

              {urlPreview && (
                <div className="flex justify-center">
                  <img src={urlPreview} alt="URL preview" className="max-h-56 rounded-lg shadow-lg border border-white/10" />
                </div>
              )}

              <Textarea
                placeholder={t('placeholderUrlQuery')}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="bg-slate-900/50 backdrop-blur-sm border border-white/10 text-gray-100 min-h-[100px] rounded-xl focus:ring-2 focus:ring-blue-500 placeholder:text-gray-500"
              />

              <Button
                onClick={handleSubmit}
                disabled={!url || loading}
                className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold py-2 rounded-xl transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : t('checkBtn')}
              </Button>
            </div>
          )}

          {/* === RESULT === */}
          {!loading && result && (
            <div className="mt-6 p-6 border border-white/10 bg-slate-900/60 backdrop-blur-md rounded-xl animate-in fade-in slide-in-from-bottom-4 shadow-2xl">
              <div className="flex items-center gap-2 text-blue-400 mb-4 border-b border-white/5 pb-2">
                <CheckCircle2 className="w-5 h-5" />
                <h3 className="font-semibold text-lg">{t('analysisResult')}</h3>
              </div>

              {/* Вердикт */}
              <div className="mb-4">
                <p className="text-xl font-bold text-white mb-1">{formatVerdict(result.verdict)}</p>
                {typeof result.confidence === 'number' && (
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-24 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500" style={{ width: `${result.confidence * 100}%` }}></div>
                    </div>
                    <p className="text-xs text-slate-400">{(result.confidence * 100).toFixed(0)}% {t('confidence')}</p>
                  </div>
                )}
              </div>

              {/* Түсіндірме */}
              {(result.explanation || result.detailed_explanation) && (
                <div className="bg-slate-800/50 rounded-lg p-3 mb-4 border border-white/5">
                  <p className="text-slate-300 text-sm leading-relaxed">{result.explanation || result.detailed_explanation}</p>
                </div>
              )}

              {/* Предвзятость */}
              {result.bias_identification && (
                <p className="mb-2 text-sm text-slate-300">
                  🎭 <span className="font-semibold text-slate-200">{t('bias')}:</span> {result.bias_identification}
                </p>
              )}

              {/* Источники */}
              {result.sources && result.sources.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-semibold mb-2 text-slate-400 uppercase tracking-wider">{t('sources')}:</h4>
                  <ul className="grid gap-2 text-sm">
                    {result.sources.map((source, index) => (
                      <li key={index}>
                        <a href={source.url} target="_blank" rel="noopener noreferrer" className="block p-2 rounded bg-slate-800/30 hover:bg-slate-800/60 border border-white/5 transition group">
                          <span className="text-blue-400 group-hover:text-blue-300 font-medium block truncate">{source.title || source.url}</span>
                          {source.description && <span className="text-slate-500 text-xs block truncate mt-0.5">{source.description}</span>}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* JSON (Debug) */}
              {showJson && (
                <pre className="text-xs bg-black/50 border border-white/10 rounded-lg p-3 mt-4 text-slate-400 overflow-x-auto">
                  {JSON.stringify(result, null, 2)}
                </pre>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Ошибка көрсету */}
      {!loading && error && (
        <div className="flex items-center gap-2 text-red-400 bg-[#2a0d0d] border border-red-800 rounded-xl p-3 mt-4 animate-in fade-in slide-in-from-top-2">
          <XCircle className="w-5 h-5 flex-shrink-0" />
          <span className="break-words">{error}</span>
        </div>
      )}
    </div>
  );
}