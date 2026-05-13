"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send, Upload, Database, FileText, Trash2, Search, Loader2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Source {
  ref: number;
  document_name: string;
  page: number;
  text: string;
  score: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  elapsed_ms?: number;
}

interface KBInfo {
  kb_id: string;
  name: string;
  chunk_count: number;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [kbs, setKBs] = useState<KBInfo[]>([]);
  const [selectedKb, setSelectedKb] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchKBs();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchKBs = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/knowledge-bases`);
      const data = await res.json();
      setKBs(data.knowledge_bases || []);
    } catch (e) {
      console.error("Failed to fetch KBs", e);
    }
  };

  const createKB = async () => {
    const name = prompt("知识库名称：");
    if (!name) return;
    try {
      await fetch(`${API_URL}/api/v1/knowledge-bases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      fetchKBs();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteKB = async (kbId: string) => {
    if (!confirm("确认删除该知识库？此操作不可撤销。")) return;
    try {
      await fetch(`${API_URL}/api/v1/knowledge-bases/${kbId}`, { method: "DELETE" });
      if (selectedKb === kbId) setSelectedKb(null);
      fetchKBs();
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedKb) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await fetch(`${API_URL}/api/v1/knowledge-bases/${selectedKb}/documents`, {
        method: "POST",
        body: formData,
      });
      fetchKBs();
    } catch (e) {
      console.error(e);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: input,
          kb_id: selectedKb || null,
          top_k: 5,
        }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources,
          elapsed_ms: data.elapsed_ms,
        },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "请求失败，请检查后端服务是否正常运行。" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen bg-[#0f1117]">
      {/* Sidebar */}
      <div className={`${showSidebar ? "w-80" : "w-0"} transition-all duration-200 border-r border-[#252830] bg-[#13151c] flex flex-col overflow-hidden`}>
        <div className="p-4 border-b border-[#252830]">
          <h1 className="text-lg font-bold text-white flex items-center gap-2">
            <Database size={20} className="text-blue-400" />
            Enterprise RAG
          </h1>
          <p className="text-xs text-gray-500 mt-1">企业知识库检索系统</p>
        </div>

        <div className="p-3 border-b border-[#252830]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-gray-400 uppercase">知识库</span>
            <button
              onClick={createKB}
              className="text-xs px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-white transition-colors"
            >
              + 新建
            </button>
          </div>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {kbs.map((kb) => (
              <div
                key={kb.kb_id}
                onClick={() => setSelectedKb(kb.kb_id)}
                className={`p-2 rounded cursor-pointer flex items-center justify-between text-sm transition-colors ${
                  selectedKb === kb.kb_id
                    ? "bg-blue-600/20 border border-blue-500/30 text-blue-300"
                    : "hover:bg-[#1e2130] text-gray-300 border border-transparent"
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <FileText size={14} className="shrink-0" />
                  <span className="truncate">{kb.name}</span>
                  <span className="text-xs text-gray-500">{kb.chunk_count}</span>
                </div>
                <button
                  onClick={(ev) => {
                    ev.stopPropagation();
                    deleteKB(kb.kb_id);
                  }}
                  className="opacity-0 hover:opacity-100 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded"
                >
                  <Trash2 size={12} className="text-red-400" />
                </button>
              </div>
            ))}
            {kbs.length === 0 && (
              <p className="text-xs text-gray-600 py-4 text-center">暂无知识库，点击"新建"创建</p>
            )}
          </div>
        </div>

        {selectedKb && (
          <div className="p-3 border-b border-[#252830]">
            <label className="flex items-center justify-center gap-2 py-3 border-2 border-dashed border-[#252830] rounded-lg cursor-pointer hover:border-blue-500/50 transition-colors text-sm text-gray-400 hover:text-blue-300">
              {uploading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Upload size={16} />
              )}
              {uploading ? "上传中..." : "上传文档 (PDF/DOCX/TXT/MD)"}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={handleUpload}
                className="hidden"
              />
            </label>
          </div>
        )}

        <div className="mt-auto p-3 border-t border-[#252830]">
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="text-xs text-gray-500 hover:text-gray-300"
          >
            {showSidebar ? "收起侧栏" : "展开侧栏"}
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="h-12 border-b border-[#252830] flex items-center px-4 gap-3 shrink-0">
          {!showSidebar && (
            <button
              onClick={() => setShowSidebar(true)}
              className="text-gray-400 hover:text-white"
            >
              <Database size={18} />
            </button>
          )}
          <span className="text-sm text-gray-400">
            {selectedKb
              ? `当前知识库: ${kbs.find((k) => k.kb_id === selectedKb)?.name || selectedKb}`
              : "全局检索 (未选择知识库)"}
          </span>
          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              className="ml-auto text-xs text-gray-500 hover:text-gray-300"
            >
              清空对话
            </button>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4">
                <Search size={28} className="text-white" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">企业知识库智能检索</h2>
              <p className="text-gray-500 max-w-md text-sm">
                上传企业文档，用自然语言提问，获取精准回答。
                <br />
                每次回答均标注引用来源，确保信息可靠可追溯。
              </p>
              <div className="flex gap-2 mt-6 flex-wrap justify-center">
                {["年假有几天？", "新员工入职需要哪些材料？", "系统架构是什么？", "五险一金比例"].map(
                  (q) => (
                    <button
                      key={q}
                      onClick={() => {
                        setInput(q);
                      }}
                      className="px-3 py-1.5 text-xs bg-[#1a1d27] hover:bg-[#252830] border border-[#2a2d3a] rounded-full text-gray-300 transition-colors"
                    >
                      {q}
                    </button>
                  )
                )}
              </div>
            </div>
          )}

          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] ${
                    msg.role === "user"
                      ? "bg-blue-600/20 border border-blue-500/30 rounded-2xl rounded-br-md px-4 py-3"
                      : "bg-[#1a1d27] border border-[#252830] rounded-2xl rounded-bl-md px-4 py-3"
                  }`}
                >
                  {msg.role === "user" ? (
                    <p className="text-sm text-gray-100 whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <div className="prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  )}

                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-[#252830]">
                      <p className="text-xs text-gray-500 mb-2 font-semibold">
                        引用来源
                        {msg.elapsed_ms && (
                          <span className="ml-2 font-normal text-gray-600">{msg.elapsed_ms}ms</span>
                        )}
                      </p>
                      <div className="space-y-1.5">
                        {msg.sources.map((src, si) => (
                          <div key={si} className="text-xs bg-[#0f1117] rounded-lg p-2 border border-[#1e2130]">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="bg-blue-600/30 text-blue-300 px-1.5 py-0.5 rounded text-[10px] font-bold">
                                [{src.ref}]
                              </span>
                              <span className="text-gray-300 font-medium">{src.document_name}</span>
                              <span className="text-gray-600">第{src.page}页</span>
                              <span className="text-gray-600 ml-auto">
                                {(src.score * 100).toFixed(1)}%
                              </span>
                            </div>
                            <p className="text-gray-500 leading-relaxed">{src.text}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-[#1a1d27] border border-[#252830] rounded-2xl rounded-bl-md px-4 py-3">
                  <Loader2 size={16} className="animate-spin text-blue-400" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="border-t border-[#252830] p-4 shrink-0">
          <div className="max-w-3xl mx-auto flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入问题，按 Enter 发送..."
              rows={1}
              className="flex-1 bg-[#1a1d27] border border-[#252830] rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-600 resize-none focus:outline-none focus:border-blue-500/50 transition-colors"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-[#1e2130] disabled:text-gray-600 text-white rounded-xl transition-colors shrink-0"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
