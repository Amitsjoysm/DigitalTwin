import React, { useState, useEffect, useRef } from 'react';
import { conversationAPI, chatAPI } from '../services/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Send, Loader2, Video } from 'lucide-react';
import { toast } from 'sonner';

export const ChatInterface = ({ conversationId, onBack }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversation, setConversation] = useState(null);
  const [videoGenerating, setVideoGenerating] = useState({});
  const scrollRef = useRef(null);

  useEffect(() => {
    if (conversationId) {
      loadConversation();
    }
  }, [conversationId]);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const loadConversation = async () => {
    try {
      const data = await conversationAPI.get(conversationId);
      setConversation(data);
      setMessages(data.messages || []);
    } catch (error) {
      toast.error('Failed to load conversation');
    }
  };

  const pollVideoStatus = async (taskId, messageIndex) => {
    setVideoGenerating(prev => ({ ...prev, [messageIndex]: true }));
    
    const maxAttempts = 60; // Poll for up to 60 seconds
    let attempts = 0;
    
    const poll = async () => {
      try {
        const status = await chatAPI.getVideoStatus(taskId);
        
        if (status.status === 'completed' && status.video_url) {
          // Update message with video URL
          setMessages(prev => {
            const newMessages = [...prev];
            if (newMessages[messageIndex]) {
              newMessages[messageIndex] = {
                ...newMessages[messageIndex],
                video_url: status.video_url,
                video_status: 'completed'
              };
            }
            return newMessages;
          });
          setVideoGenerating(prev => ({ ...prev, [messageIndex]: false }));
          toast.success('Video ready!');
          return;
        } else if (status.status === 'failed') {
          setVideoGenerating(prev => ({ ...prev, [messageIndex]: false }));
          toast.error('Video generation failed');
          return;
        }
        
        // Continue polling
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000); // Poll every 2 seconds
        } else {
          setVideoGenerating(prev => ({ ...prev, [messageIndex]: false }));
          toast.error('Video generation timeout');
        }
      } catch (error) {
        setVideoGenerating(prev => ({ ...prev, [messageIndex]: false }));
        console.error('Error polling video status:', error);
      }
    };
    
    poll();
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await chatAPI.sendMessage(conversationId, input);
      const assistantMessage = {
        ...response.message,
        video_task_id: response.video_task_id,
        video_status: response.video_task_id ? 'generating' : null
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      if (response.video_task_id) {
        const messageIndex = messages.length + 1; // User message + assistant message
        toast.info('Generating video response...');
        pollVideoStatus(response.video_task_id, messageIndex);
      }
    } catch (error) {
      console.error('Send message error:', error);
      toast.error('Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full" data-testid="chat-interface">
      <div className="p-4 border-b flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold" data-testid="conversation-title">
            {conversation?.title || 'Conversation'}
          </h2>
          <p className="text-sm text-muted-foreground">
            {messages.length} messages
          </p>
        </div>
        <Button variant="outline" onClick={onBack} data-testid="back-button">
          Back
        </Button>
      </div>

      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              data-testid={`message-${message.role}-${index}`}
            >
              {message.role === 'assistant' && (
                <Avatar className="h-8 w-8">
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
              )}
              <div className="flex flex-col gap-2 max-w-[70%]">
                <Card
                  className={`p-3 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  {message.response_time_ms && (
                    <p className="text-xs opacity-70 mt-1">
                      {message.response_time_ms}ms
                    </p>
                  )}
                </Card>
                
                {/* Video Player for AI responses */}
                {message.role === 'assistant' && (
                  <div>
                    {message.video_url && (
                      <Card className="p-2 bg-black">
                        <video
                          src={message.video_url}
                          controls
                          autoPlay
                          className="w-full rounded"
                          style={{ maxWidth: '400px' }}
                        >
                          Your browser does not support video playback.
                        </video>
                      </Card>
                    )}
                    
                    {message.video_status === 'generating' && videoGenerating[index] && (
                      <Card className="p-3 bg-muted flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">Generating video...</span>
                      </Card>
                    )}
                  </div>
                )}
              </div>
              {message.role === 'user' && (
                <Avatar className="h-8 w-8">
                  <AvatarFallback>You</AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Input
            data-testid="message-input"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <Button
            data-testid="send-message-button"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            size="icon"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
};