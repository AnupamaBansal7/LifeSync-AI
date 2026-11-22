import { useEffect, useRef, useState } from 'react';

export interface UseVoiceConversationOptions {
  onTranscript?: (text: string) => void;
  lang?: string;
}

export function useVoiceConversation(options: UseVoiceConversationOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [voiceReadbackEnabled, setVoiceReadbackEnabled] = useState<boolean>(() => {
    try {
      return localStorage.getItem('lifesync_voice_readback') === 'true';
    } catch {
      return false;
    }
  });

  const recognitionRef = useRef<any>(null);
  const onTranscriptRef = useRef(options.onTranscript);
  onTranscriptRef.current = options.onTranscript;

  useEffect(() => {
    try {
      localStorage.setItem('lifesync_voice_readback', String(voiceReadbackEnabled));
    } catch {
      // ignore
    }
  }, [voiceReadbackEnabled]);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      setIsSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = options.lang || 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript || '';
        if (transcript.trim() && onTranscriptRef.current) {
          onTranscriptRef.current(transcript.trim());
        }
        setIsListening(false);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    } else {
      setIsSupported(false);
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [options.lang]);

  const toggleListening = (callbackOverride?: (text: string) => void) => {
    if (!recognitionRef.current) return;

    if (callbackOverride) {
      onTranscriptRef.current = callbackOverride;
    }

    // If currently speaking, stop voice synthesis before listening
    if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }

    if (isListening) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch {
        setIsListening(false);
      }
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      setIsListening(false);
    }
  };

  const speak = (text: string, force: boolean = false) => {
    if (!('speechSynthesis' in window)) return;
    if (!voiceReadbackEnabled && !force) return;

    window.speechSynthesis.cancel();
    if (!text.trim()) return;

    // Clean markdown symbols for cleaner voice narration
    const cleanText = text
      .replace(/[#*_`~>-]/g, ' ')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/\s+/g, ' ')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  return {
    isListening,
    isSpeaking,
    isSupported,
    voiceReadbackEnabled,
    setVoiceReadbackEnabled,
    toggleListening,
    stopListening,
    speak,
    stopSpeaking,
  };
}
