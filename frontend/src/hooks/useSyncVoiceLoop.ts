import { useCallback, useEffect, useRef, useState } from 'react';

export type VoiceState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';

export interface UseSyncVoiceLoopOptions {
  onSendMessage?: (message: string) => Promise<void>;
  lang?: string;
  autoSpeakAssistant?: boolean;
}

export function useSyncVoiceLoop({
  onSendMessage,
  lang = 'en-US',
}: UseSyncVoiceLoopOptions = {}) {
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [handsFreeEnabled, setHandsFreeEnabled] = useState<boolean>(() => {
    try {
      return localStorage.getItem('lifesync_hands_free_voice') === 'true';
    } catch {
      return false;
    }
  });
  const [transcript, setTranscript] = useState<string>('');
  const [isSupported, setIsSupported] = useState<boolean>(false);

  const recognitionRef = useRef<any>(null);
  const handsFreeRef = useRef<boolean>(handsFreeEnabled);
  handsFreeRef.current = handsFreeEnabled;

  const voiceStateRef = useRef<VoiceState>(voiceState);
  voiceStateRef.current = voiceState;

  const onSendMessageRef = useRef(onSendMessage);
  onSendMessageRef.current = onSendMessage;

  const silenceTimerRef = useRef<any>(null);
  const accumulatedTranscriptRef = useRef<string>('');

  // Persist hands-free preference
  useEffect(() => {
    try {
      localStorage.setItem('lifesync_hands_free_voice', String(handsFreeEnabled));
    } catch {
      // ignore
    }
  }, [handsFreeEnabled]);

  // Barge-in: cancels speech synthesis
  const cancelSpeaking = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      if (voiceStateRef.current === 'SPEAKING') {
        setVoiceState('IDLE');
      }
    }
  }, []);

  // Safe start of recognition
  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    cancelSpeaking();

    try {
      accumulatedTranscriptRef.current = '';
      setTranscript('');
      recognitionRef.current.start();
      setVoiceState('LISTENING');
    } catch (e: any) {
      // If already started, do nothing
      if (e?.name !== 'InvalidStateError') {
        console.warn('Speech recognition start error:', e);
      }
    }
  }, [cancelSpeaking]);

  // Safe stop of recognition
  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop();
    } catch {
      // ignore
    }
    if (voiceStateRef.current === 'LISTENING') {
      setVoiceState('IDLE');
    }
  }, []);

  // Initialize SpeechRecognition
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
      return;
    }

    setIsSupported(true);
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = lang;

    recognition.onresult = (event: any) => {
      let finalStr = '';
      let interimStr = '';

      for (let i = 0; i < event.results.length; i++) {
        const res = event.results[i];
        if (res.isFinal) {
          finalStr += res[0].transcript;
        } else {
          interimStr += res[0].transcript;
        }
      }

      const currentText = (finalStr || interimStr).trim();
      if (currentText) {
        setTranscript(currentText);
        accumulatedTranscriptRef.current = currentText;

        // Reset silence timer on incoming words
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
        }

        // In hands-free mode, if we have a non-empty final result or pause, submit
        if (finalStr.trim() && handsFreeRef.current) {
          silenceTimerRef.current = setTimeout(() => {
            const textToSubmit = accumulatedTranscriptRef.current.trim();
            if (textToSubmit && onSendMessageRef.current) {
              setVoiceState('THINKING');
              stopListening();
              onSendMessageRef.current(textToSubmit);
              accumulatedTranscriptRef.current = '';
              setTranscript('');
            }
          }, 800);
        }
      }
    };

    recognition.onerror = (err: any) => {
      // 'no-speech' is expected during pauses
      if (err.error !== 'no-speech') {
        console.warn('Speech recognition event error:', err.error);
      }
      if (voiceStateRef.current === 'LISTENING') {
        setVoiceState('IDLE');
      }
    };

    recognition.onend = () => {
      // If hands-free is enabled and we stopped without thinking/speaking, auto-resume
      if (handsFreeRef.current && voiceStateRef.current === 'LISTENING') {
        setTimeout(() => {
          if (handsFreeRef.current && voiceStateRef.current === 'LISTENING') {
            try {
              recognition.start();
            } catch {
              setVoiceState('IDLE');
            }
          }
        }, 300);
      } else if (voiceStateRef.current === 'LISTENING') {
        setVoiceState('IDLE');
      }
    };

    recognitionRef.current = recognition;

    return () => {
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      try {
        recognition.abort();
      } catch {
        // ignore
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [lang, stopListening]);

  // Clean, speak assistant text and handle hands-free loop chaining
  const speakText = useCallback(
    (text: string, onEndCallback?: () => void) => {
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
        if (onEndCallback) onEndCallback();
        return;
      }

      // Stop any existing speech or listening to avoid echo feedback
      window.speechSynthesis.cancel();
      stopListening();

      if (!text || !text.trim()) {
        if (onEndCallback) onEndCallback();
        return;
      }

      // Clean markdown and non-verbal tokens
      const clean = text
        .replace(/[#*_`~>-]/g, ' ')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/\{[^\}]*\}/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

      const utterance = new SpeechSynthesisUtterance(clean);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      utterance.lang = lang;

      utterance.onstart = () => {
        setVoiceState('SPEAKING');
      };

      utterance.onend = () => {
        setVoiceState('IDLE');
        if (onEndCallback) {
          onEndCallback();
        } else if (handsFreeRef.current) {
          // In hands-free mode, resume listening 400ms after speech completes (anti-echo delay)
          setTimeout(() => {
            if (handsFreeRef.current) {
              startListening();
            }
          }, 400);
        }
      };

      utterance.onerror = () => {
        setVoiceState('IDLE');
        if (handsFreeRef.current) {
          setTimeout(() => {
            if (handsFreeRef.current) startListening();
          }, 300);
        }
      };

      window.speechSynthesis.speak(utterance);
    },
    [lang, startListening, stopListening]
  );

  const toggleHandsFree = useCallback(() => {
    setHandsFreeEnabled((prev) => {
      const next = !prev;
      if (next) {
        startListening();
      } else {
        stopListening();
        cancelSpeaking();
      }
      return next;
    });
  }, [cancelSpeaking, startListening, stopListening]);

  const togglePushToTalk = useCallback(() => {
    if (voiceState === 'LISTENING') {
      stopListening();
    } else {
      startListening();
    }
  }, [voiceState, startListening, stopListening]);

  return {
    voiceState,
    setVoiceState,
    handsFreeEnabled,
    setHandsFreeEnabled,
    toggleHandsFree,
    isListening: voiceState === 'LISTENING',
    isSpeaking: voiceState === 'SPEAKING',
    isThinking: voiceState === 'THINKING',
    transcript,
    setTranscript,
    isSupported,
    startListening,
    stopListening,
    speakText,
    cancelSpeaking,
    togglePushToTalk,
  };
}
