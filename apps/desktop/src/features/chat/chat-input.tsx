import React, { useState, useRef, useEffect } from 'react';
import { Paperclip, Globe, ArrowUp, X, File as FileIcon, FileText, Image as ImageIcon, FileType, AlertCircle, Mic, MicOff, ChevronDown, Sparkles, Search } from 'lucide-react';

interface SendOptions {
  deepResearch: boolean;
  files: File[];
  model: string;
  mode: string;
}

interface ChatInputProps {
  onSend: ((text: string, options: SendOptions) => void) | ((text: string) => void);
  disabled?: boolean;
  isInitial?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled, isInitial = false }) => {
  const [text, setText] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [isDeepResearch, setIsDeepResearch] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  
  const [mode, setMode] = useState('Agent');
  const [isModeMenuOpen, setIsModeMenuOpen] = useState(false);
  
  const AVAILABLE_MODELS = [
    { id: 'gemini-3-flash-preview', name: 'Gemini 3 Flash' },
    { id: 'gemini-3.1-flash-lite-preview', name: 'Gemini 3.1 Flash' },
    { id: 'gemini-3.1-pro-preview', name: 'Gemini 3.1 Pro' }
  ];
  
  const [model, setModel] = useState('gemini-3-flash-preview');
  const [isModelMenuOpen, setIsModelMenuOpen] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  const modeMenuRef = useRef<HTMLDivElement>(null);
  const modelMenuRef = useRef<HTMLDivElement>(null);
  
  const dragCounter = useRef(0);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modeMenuRef.current && !modeMenuRef.current.contains(event.target as Node)) {
        setIsModeMenuOpen(false);
      }
      if (modelMenuRef.current && !modelMenuRef.current.contains(event.target as Node)) {
        setIsModelMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 240) + 'px';
    }
  }, [text]);

  useEffect(() => {
      if (errorMsg) {
          const timer = setTimeout(() => setErrorMsg(null), 3000);
          return () => clearTimeout(timer);
      }
  }, [errorMsg]);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onresult = (event: any) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        if (finalTranscript) {
          setText(prev => prev + (prev ? ' ' : '') + finalTranscript);
        }
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error("Speech recognition error", event.error);
        setIsRecording(false);
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
      };
    }
  }, []);

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
    } else {
      setText('');
      recognitionRef.current?.start();
      setIsRecording(true);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if ((text.trim() || files.length > 0) && !disabled) {
      onSend(text, { deepResearch: isDeepResearch, files, model, mode });
      setText('');
      setFiles([]);
      if (isRecording) {
        recognitionRef.current?.stop();
        setIsRecording(false);
      }
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }
  };

  const validateAndAddFiles = (newFiles: File[]) => {
      const allowedTypes = [
          'application/pdf', 
          'text/plain', 
          'text/html', 
          'text/markdown', 
          'image/png', 
          'image/jpeg', 
          'image/webp', 
          'image/gif'
      ];
      
      const validFiles: File[] = [];
      let hasInvalid = false;

      newFiles.forEach(file => {
          const isText = file.name.endsWith('.txt') || file.name.endsWith('.md') || file.name.endsWith('.html');
          
          if (allowedTypes.includes(file.type) || isText) {
              validFiles.push(file);
          } else {
              hasInvalid = true;
          }
      });

      if (hasInvalid) {
          setErrorMsg("Supported formats: PDF, Text, HTML, Images.");
      }

      if (validFiles.length > 0) {
          setFiles(prev => [...prev, ...validFiles]);
      }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      validateAndAddFiles(Array.from(e.target.files));
    }
    e.target.value = '';
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleDragEnter = (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current += 1;
      if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
          setIsDragging(true);
      }
  };

  const handleDragLeave = (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current -= 1;
      if (dragCounter.current === 0) {
          setIsDragging(false);
      }
  };

  const handleDragOver = (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (!isDragging) setIsDragging(true);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        validateAndAddFiles(Array.from(e.dataTransfer.files));
    }
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return null;
    if (file.type === 'application/pdf') return <FileType className="w-6 h-6 text-red-500" />;
    if (file.type.startsWith('text/') || file.name.endsWith('.html') || file.name.endsWith('.md')) return <FileText className="w-6 h-6 text-blue-500" />;
    return <FileIcon className="text-zinc-500 dark:text-zinc-400 w-6 h-6" />;
  };

  const containerClasses = isInitial 
    ? "w-full relative" 
    : "absolute bottom-0 left-0 right-0 z-30 pointer-events-none";

  return (
    <div className={containerClasses}>
      {!isInitial && (
        <>
          <div className="absolute left-0 right-0 h-10 bg-gradient-to-t from-white to-transparent dark:from-[#1a1a1a] pointer-events-none" style={{ top: '-40px' }} />
          <div className="absolute inset-0 bg-white dark:bg-[#1a1a1a] pointer-events-none" />
        </>
      )}

      <div className={`relative flex justify-center w-full ${!isInitial ? 'px-4 pb-6' : ''}`}>
        <div className="w-full max-w-5xl pointer-events-auto">
          
          <div 
              className={`
                  relative flex flex-col w-full 
                  bg-[#f4f4f4] dark:bg-zinc-800/80 
                  border 
                  rounded-2xl shadow-sm dark:shadow-black/40
                  transition-all duration-300 ease-in-out
                  ${disabled ? 'opacity-70 cursor-not-allowed' : ''}
                  ${isDragging ? 'border-primary ring-2 ring-primary/20 bg-blue-50 dark:bg-zinc-800/80 scale-[1.01]' : 'border-zinc-200/50 dark:border-zinc-700/50'}
                  ${isRecording ? 'border-red-400 ring-2 ring-red-500/20' : ''}
                  focus-within:border-zinc-300 dark:focus-within:border-zinc-600
                  focus-within:ring-1 focus-within:ring-zinc-200 dark:focus-within:ring-zinc-700
              `}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
          >
            {isDragging && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-white/80 dark:bg-black/80 backdrop-blur-sm rounded-2xl border-2 border-dashed border-primary pointer-events-none">
                    <div className="flex flex-col items-center animate-bounce">
                        <Paperclip className="w-8 h-8 text-primary mb-2" />
                        <span className="text-sm font-bold text-primary">Drop files to attach</span>
                    </div>
                </div>
            )}
            
            {errorMsg && (
                <div className="absolute -top-12 left-0 right-0 flex justify-center animate-fade-in pointer-events-none">
                    <div className="bg-red-500 text-white px-4 py-2 rounded-full shadow-lg text-sm font-medium flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        {errorMsg}
                    </div>
                </div>
            )}

            {files.length > 0 && (
              <div className="flex flex-wrap gap-2 px-4 pt-4">
                {files.map((file, i) => (
                  <div key={i} className="relative group w-16 h-16 rounded-xl overflow-hidden bg-white dark:bg-zinc-700 border border-zinc-200 dark:border-zinc-600 shadow-sm flex items-center justify-center">
                    {file.type.startsWith('image/') ? (
                      <img src={URL.createObjectURL(file)} alt="preview" className="w-full h-full object-cover opacity-90" />
                    ) : (
                      <div className="flex flex-col items-center justify-center p-1">
                          {getFileIcon(file)}
                          <span className="text-[9px] text-zinc-500 mt-1 truncate max-w-full px-1">{file.name.slice(-6)}</span>
                      </div>
                    )}
                    <button 
                      onClick={() => removeFile(i)}
                      className="absolute top-0.5 right-0.5 bg-black/60 hover:bg-black/80 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-all z-10"
                    >
                      <X size={10} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <textarea
              ref={textareaRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isRecording ? "Listening..." : "Plan, @ for context, / for commands"}
              disabled={disabled}
              className="w-full bg-transparent border-none outline-none text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 px-5 pt-4 pb-2 text-base resize-none min-h-[60px] max-h-[240px] custom-scrollbar"
              rows={1}
            />

            <div className="flex items-center justify-between p-2 pl-4">
              
              {/* Left Actions */}
              <div className="flex items-center gap-3">
                  
                  {/* Mode Dropdown */}
                  <div className="relative" ref={modeMenuRef}>
                    <button 
                      onClick={() => setIsModeMenuOpen(!isModeMenuOpen)}
                      className={`flex items-center gap-1.5 text-sm font-medium transition-colors px-2.5 py-1.5 rounded-xl ${isModeMenuOpen ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100' : 'text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800'}`}
                    >
                      <span className="text-lg leading-none mb-0.5">∞</span> {mode} <ChevronDown className="w-3.5 h-3.5 opacity-70" />
                    </button>
                    {isModeMenuOpen && (
                      <div className="absolute bottom-full left-0 mb-2 w-32 bg-[#1a1a1a] border border-zinc-800 rounded-xl shadow-xl z-50 py-1 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
                        {['Agent', 'Plan'].map(m => (
                          <button 
                            key={m}
                            onClick={() => { setMode(m); setIsModeMenuOpen(false); }}
                            className="w-full text-left px-3 py-2 text-sm hover:bg-zinc-800 flex items-center justify-between text-zinc-300"
                          >
                            <div className="flex items-center gap-2">
                              {m === 'Agent' ? <span className="text-lg leading-none">∞</span> : <span className="text-lg leading-none">✓</span>}
                              {m}
                            </div>
                            {mode === m && <span className="text-xs">✓</span>}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Model Dropdown */}
                  <div className="relative" ref={modelMenuRef}>
                    <button 
                      onClick={() => setIsModelMenuOpen(!isModelMenuOpen)}
                      className={`flex items-center gap-1.5 text-sm font-medium transition-colors px-2.5 py-1.5 rounded-xl ${isModelMenuOpen ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100' : 'text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800'}`}
                    >
                      <Sparkles className="w-3.5 h-3.5" /> {AVAILABLE_MODELS.find(m => m.id === model)?.name || 'Gemini 3 Flash'} <ChevronDown className="w-3.5 h-3.5 opacity-70" />
                    </button>
                    {isModelMenuOpen && (
                      <div className="absolute bottom-full left-0 mb-2 w-64 bg-[#1a1a1a] border border-zinc-800 rounded-xl shadow-xl z-50 py-2 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
                        <div className="px-3 pb-2 mb-2 border-b border-zinc-800 flex items-center justify-between">
                          <div className="flex items-center gap-2 text-zinc-400 text-sm">
                            <Search className="w-4 h-4" />
                            <input type="text" placeholder="Search models..." className="bg-transparent outline-none w-full" />
                          </div>
                        </div>
                        <div className="px-3 py-2 flex items-center justify-between hover:bg-zinc-800 cursor-pointer" onClick={() => setIsDeepResearch(!isDeepResearch)}>
                          <div className="flex items-center gap-2 text-zinc-300 text-sm">
                            <Globe className="w-4 h-4" /> Thinking
                          </div>
                          <div className={`w-8 h-4 rounded-full transition-colors ${isDeepResearch ? 'bg-blue-600' : 'bg-zinc-600'} relative`}>
                            <div className={`absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-white transition-transform ${isDeepResearch ? 'translate-x-4' : ''}`} />
                          </div>
                        </div>
                        <div className="h-px bg-zinc-800 my-1" />
                        {AVAILABLE_MODELS.map(m => (
                          <button 
                            key={m.id}
                            onClick={() => { setModel(m.id); setIsModelMenuOpen(false); }}
                            className={`w-full text-left px-3 py-2 text-sm hover:bg-zinc-800 flex items-center gap-2 ${model === m.id ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-400'}`}
                          >
                            <Sparkles className="w-4 h-4" /> {m.name}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
              </div>

              {/* Right Actions */}
              <div className="flex items-center gap-2">
                  <div className="relative group">
                      <button 
                          onClick={() => fileInputRef.current?.click()}
                          className="flex items-center justify-center h-9 w-9 text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200 transition-colors"
                          title="Upload file"
                      >
                          <Paperclip className="w-5 h-5" />
                      </button>
                      <input 
                          type="file" 
                          multiple 
                          ref={fileInputRef} 
                          className="hidden" 
                          onChange={handleFileSelect} 
                          accept=".pdf,.txt,.md,.html,.png,.jpg,.jpeg,.webp,.gif"
                      />
                  </div>

                  <button 
                      onClick={toggleRecording}
                      className={`flex items-center justify-center h-9 w-9 rounded-full transition-colors ${
                        isRecording 
                          ? 'bg-red-100 text-red-500 dark:bg-red-900/30 dark:text-red-400 animate-pulse' 
                          : 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 hover:opacity-90'
                      }`}
                      title={isRecording ? "Stop recording" : "Voice input"}
                  >
                      {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                  </button>

                  {text.trim() || files.length > 0 ? (
                    <button 
                        onClick={handleSubmit}
                        disabled={disabled}
                        className={`
                            h-9 w-9 flex items-center justify-center rounded-full transition-all duration-200
                            bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 hover:opacity-90 shadow-md
                        `}
                    >
                        <ArrowUp className="w-5 h-5" strokeWidth={2.5} />
                    </button>
                  ) : null}
              </div>
            </div>
          </div>
          
          {!isInitial && (
            <div className="text-center mt-3 text-xs text-zinc-400 dark:text-zinc-500 font-medium relative z-10">
               Dexpert AI can make mistakes. Check important info.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
