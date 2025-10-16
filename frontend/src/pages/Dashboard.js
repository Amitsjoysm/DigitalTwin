import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { conversationAPI, knowledgeAPI } from '../services/api';
import { ChatInterface } from '../components/ChatInterface';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ScrollArea } from '../components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import { MessageSquare, Plus, Upload, BookOpen, User, LogOut, Trash2 } from 'lucide-react';

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [knowledge, setKnowledge] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [showKnowledge, setShowKnowledge] = useState(false);
  const [uploadingKnowledge, setUploadingKnowledge] = useState(false);

  useEffect(() => {
    loadConversations();
    loadKnowledge();
  }, []);

  const loadConversations = async () => {
    try {
      const data = await conversationAPI.list();
      setConversations(data);
    } catch (error) {
      toast.error('Failed to load conversations');
    }
  };

  const loadKnowledge = async () => {
    try {
      const data = await knowledgeAPI.list();
      setKnowledge(data);
    } catch (error) {
      console.error('Failed to load knowledge');
    }
  };

  const createNewConversation = async () => {
    try {
      const conversation = await conversationAPI.create();
      setConversations([conversation, ...conversations]);
      setSelectedConversation(conversation.id);
      toast.success('New conversation started');
    } catch (error) {
      toast.error('Failed to create conversation');
    }
  };

  const handleDeleteConversation = async (id) => {
    try {
      await conversationAPI.delete(id);
      setConversations(conversations.filter(c => c.id !== id));
      if (selectedConversation === id) {
        setSelectedConversation(null);
      }
      toast.success('Conversation deleted');
    } catch (error) {
      toast.error('Failed to delete conversation');
    }
  };

  const handleUploadKnowledge = async (file) => {
    setUploadingKnowledge(true);
    try {
      await knowledgeAPI.upload(file);
      loadKnowledge();
      toast.success('Knowledge uploaded successfully');
    } catch (error) {
      toast.error('Failed to upload knowledge');
    } finally {
      setUploadingKnowledge(false);
    }
  };

  const handleDeleteKnowledge = async (id) => {
    try {
      await knowledgeAPI.delete(id);
      setKnowledge(knowledge.filter(k => k.id !== id));
      toast.success('Knowledge deleted');
    } catch (error) {
      toast.error('Failed to delete knowledge');
    }
  };

  if (selectedConversation) {
    return (
      <ChatInterface
        conversationId={selectedConversation}
        onBack={() => setSelectedConversation(null)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-background" data-testid="dashboard">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
              {user?.name?.[0]?.toUpperCase()}
            </div>
            <div>
              <h1 className="text-xl font-bold" data-testid="user-name">Digital Self</h1>
              <p className="text-sm text-muted-foreground">{user?.name}</p>
            </div>
          </div>
          <Button variant="outline" onClick={logout} data-testid="logout-button">
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Conversations */}
          <div className="lg:col-span-2">
            <Card data-testid="conversations-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Conversations
                  </CardTitle>
                  <Button onClick={createNewConversation} size="sm" data-testid="new-conversation-button">
                    <Plus className="h-4 w-4 mr-2" />
                    New Chat
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  {conversations.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <p>No conversations yet</p>
                      <p className="text-sm">Start a new chat to begin</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {conversations.map((conv) => (
                        <div
                          key={conv.id}
                          className="p-3 border rounded-lg hover:bg-muted cursor-pointer flex items-center justify-between"
                          data-testid={`conversation-item-${conv.id}`}
                        >
                          <div
                            className="flex-1"
                            onClick={() => setSelectedConversation(conv.id)}
                          >
                            <p className="font-medium">{conv.title}</p>
                            <p className="text-sm text-muted-foreground">
                              {conv.message_count} messages
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteConversation(conv.id);
                            }}
                            data-testid={`delete-conversation-${conv.id}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Stats */}
            <Card data-testid="stats-card">
              <CardHeader>
                <CardTitle>Quick Stats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Conversations</span>
                    <span className="font-bold">{conversations.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Knowledge Base</span>
                    <span className="font-bold">{knowledge.length} items</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Avatar Status</span>
                    <span className="font-bold text-green-500">Active</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Knowledge Base */}
            <Card data-testid="knowledge-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  Knowledge Base
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Dialog>
                  <DialogTrigger asChild>
                    <Button className="w-full mb-4" variant="outline" data-testid="upload-knowledge-button">
                      <Upload className="h-4 w-4 mr-2" />
                      Upload Document
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Upload Knowledge</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <input
                        type="file"
                        accept=".pdf,.txt"
                        onChange={(e) => {
                          if (e.target.files[0]) {
                            handleUploadKnowledge(e.target.files[0]);
                          }
                        }}
                        disabled={uploadingKnowledge}
                        data-testid="knowledge-file-input"
                      />
                      {uploadingKnowledge && <p>Uploading...</p>}
                    </div>
                  </DialogContent>
                </Dialog>

                <ScrollArea className="h-[200px]">
                  {knowledge.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center">
                      No knowledge yet
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {knowledge.map((item) => (
                        <div
                          key={item.id}
                          className="p-2 border rounded flex items-center justify-between"
                          data-testid={`knowledge-item-${item.id}`}
                        >
                          <p className="text-sm truncate flex-1">{item.title}</p>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteKnowledge(item.id)}
                            data-testid={`delete-knowledge-${item.id}`}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};