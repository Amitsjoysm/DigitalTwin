import React, { useState, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Slider } from './ui/slider';
import { avatarAPI, userAPI } from '../services/api';
import { toast } from 'sonner';
import Webcam from 'react-webcam';
import { Video, Mic, Settings, CheckCircle, Circle, Square, Play } from 'lucide-react';

const steps = [
  { id: 1, title: 'Profile Setup', icon: Settings },
  { id: 2, title: 'Record Video', icon: Video },
  { id: 3, title: 'Voice Training', icon: Mic },
  { id: 4, title: 'Personality', icon: Settings },
  { id: 5, title: 'Complete', icon: CheckCircle }
];

export const OnboardingFlow = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const { user, updateUser } = useAuth();
  
  // Step 2: Video Recording
  const webcamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedChunks, setRecordedChunks] = useState([]);
  const [videoBlob, setVideoBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [currentExpression, setCurrentExpression] = useState(0);
  const timerRef = useRef(null);
  
  const expressions = [
    { name: 'Neutral', duration: 30, instruction: 'Look at the camera naturally' },
    { name: 'Happy/Smiling', duration: 30, instruction: 'Smile and show happiness' },
    { name: 'Thinking/Serious', duration: 30, instruction: 'Look thoughtful and serious' },
    { name: 'Talking', duration: 90, instruction: 'Talk naturally about your day or interests' }
  ];
  
  // Step 3: Voice Recording
  const [isRecordingVoice, setIsRecordingVoice] = useState(false);
  const [voiceBlob, setVoiceBlob] = useState(null);
  const [voiceRecordingTime, setVoiceRecordingTime] = useState(0);
  const [currentTextIndex, setCurrentTextIndex] = useState(0);
  const audioRecorderRef = useRef(null);
  const voiceTimerRef = useRef(null);
  
  const readingTexts = [
    "Hello, I am creating my digital self today.",
    "Technology has transformed the way we communicate.",
    "I enjoy exploring new ideas and learning every day.",
    "The quick brown fox jumps over the lazy dog.",
    "Artificial intelligence is reshaping our future.",
    "I believe in the power of human creativity.",
    "Every conversation is an opportunity to connect.",
    "Life is a beautiful journey of discovery.",
    "Innovation starts with asking the right questions.",
    "Together we can build amazing things."
  ];
  
  // Step 4: Personality
  const [personality, setPersonality] = useState({
    formality: 5,
    enthusiasm: 5,
    verbosity: 5,
    humor: 5
  });

  const nextStep = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleVideoUpload = async () => {
    if (!videoFile) {
      toast.error('Please select a video file');
      return;
    }

    setLoading(true);
    try {
      const response = await avatarAPI.upload(videoFile);
      toast.success('Video uploaded! Training started...');
      nextStep();
    } catch (error) {
      toast.error('Failed to upload video');
    } finally {
      setLoading(false);
    }
  };

  const handlePersonalitySetup = async () => {
    setLoading(true);
    try {
      const updatedUser = await userAPI.updateProfile({
        personality,
        onboarding_completed: true
      });
      updateUser(updatedUser);
      nextStep();
    } catch (error) {
      toast.error('Failed to save personality');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = () => {
    onComplete();
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4" data-testid="onboarding-step-1">
            <div className="text-center space-y-2">
              <h3 className="text-2xl font-bold">Welcome to Digital Self!</h3>
              <p className="text-muted-foreground">
                Let's create your AI-powered digital clone in just a few minutes.
              </p>
            </div>
            <div className="space-y-2">
              <Label>Your Name</Label>
              <Input value={user?.name} disabled />
            </div>
            <Button onClick={nextStep} className="w-full" data-testid="step-1-next-button">
              Get Started
            </Button>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4" data-testid="onboarding-step-2">
            <div className="text-center space-y-2">
              <Video className="h-12 w-12 mx-auto text-primary" />
              <h3 className="text-2xl font-bold">Record Your Video</h3>
              <p className="text-muted-foreground">
                Upload a 2-3 minute video of yourself talking to the camera.
              </p>
            </div>
            <div className="border-2 border-dashed rounded-lg p-8 text-center">
              <input
                data-testid="video-upload-input"
                type="file"
                accept="video/*"
                onChange={(e) => setVideoFile(e.target.files[0])}
                className="hidden"
                id="video-upload"
              />
              <label htmlFor="video-upload" className="cursor-pointer">
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-sm font-medium">
                  {videoFile ? videoFile.name : 'Click to upload video'}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  MP4, WebM, or MOV (max 100MB)
                </p>
              </label>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={prevStep} className="flex-1">
                Back
              </Button>
              <Button
                onClick={handleVideoUpload}
                disabled={!videoFile || loading}
                className="flex-1"
                data-testid="upload-video-button"
              >
                {loading ? 'Uploading...' : 'Upload & Continue'}
              </Button>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4" data-testid="onboarding-step-3">
            <div className="text-center space-y-2">
              <Mic className="h-12 w-12 mx-auto text-primary" />
              <h3 className="text-2xl font-bold">Voice Training</h3>
              <p className="text-muted-foreground">
                Voice cloning will be trained from your video automatically.
              </p>
            </div>
            <div className="bg-muted rounded-lg p-6 text-center">
              <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-500" />
              <p className="font-medium">Voice training in progress</p>
              <p className="text-sm text-muted-foreground mt-1">
                This happens automatically from your video
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={prevStep} className="flex-1">
                Back
              </Button>
              <Button onClick={nextStep} className="flex-1" data-testid="step-3-next-button">
                Continue
              </Button>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6" data-testid="onboarding-step-4">
            <div className="text-center space-y-2">
              <Settings className="h-12 w-12 mx-auto text-primary" />
              <h3 className="text-2xl font-bold">Personality Configuration</h3>
              <p className="text-muted-foreground">
                Customize how your digital self communicates
              </p>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Formality</Label>
                  <span className="text-sm text-muted-foreground">{personality.formality}/10</span>
                </div>
                <Slider
                  data-testid="formality-slider"
                  value={[personality.formality]}
                  onValueChange={([value]) => setPersonality({ ...personality, formality: value })}
                  min={1}
                  max={10}
                  step={1}
                />
                <p className="text-xs text-muted-foreground">
                  {personality.formality > 7 ? 'Formal' : personality.formality < 4 ? 'Casual' : 'Balanced'}
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Enthusiasm</Label>
                  <span className="text-sm text-muted-foreground">{personality.enthusiasm}/10</span>
                </div>
                <Slider
                  data-testid="enthusiasm-slider"
                  value={[personality.enthusiasm]}
                  onValueChange={([value]) => setPersonality({ ...personality, enthusiasm: value })}
                  min={1}
                  max={10}
                  step={1}
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Verbosity</Label>
                  <span className="text-sm text-muted-foreground">{personality.verbosity}/10</span>
                </div>
                <Slider
                  data-testid="verbosity-slider"
                  value={[personality.verbosity]}
                  onValueChange={([value]) => setPersonality({ ...personality, verbosity: value })}
                  min={1}
                  max={10}
                  step={1}
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Humor</Label>
                  <span className="text-sm text-muted-foreground">{personality.humor}/10</span>
                </div>
                <Slider
                  data-testid="humor-slider"
                  value={[personality.humor]}
                  onValueChange={([value]) => setPersonality({ ...personality, humor: value })}
                  min={1}
                  max={10}
                  step={1}
                />
              </div>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={prevStep} className="flex-1">
                Back
              </Button>
              <Button
                onClick={handlePersonalitySetup}
                disabled={loading}
                className="flex-1"
                data-testid="save-personality-button"
              >
                {loading ? 'Saving...' : 'Save & Complete'}
              </Button>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-4 text-center" data-testid="onboarding-step-5">
            <CheckCircle className="h-20 w-20 mx-auto text-green-500" />
            <h3 className="text-3xl font-bold">All Set!</h3>
            <p className="text-muted-foreground">
              Your digital self is ready. Start having conversations now!
            </p>
            <Button onClick={handleComplete} className="w-full" data-testid="complete-onboarding-button">
              Go to Dashboard
            </Button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <div className="flex justify-between items-center mb-4">
            {steps.map((step) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.id}
                  className={`flex flex-col items-center ${
                    step.id === currentStep
                      ? 'text-primary'
                      : step.id < currentStep
                      ? 'text-green-500'
                      : 'text-muted-foreground'
                  }`}
                >
                  <div
                    className={`h-10 w-10 rounded-full flex items-center justify-center ${
                      step.id === currentStep
                        ? 'bg-primary text-primary-foreground'
                        : step.id < currentStep
                        ? 'bg-green-500 text-white'
                        : 'bg-muted'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <p className="text-xs mt-1 hidden sm:block">{step.title}</p>
                </div>
              );
            })}
          </div>
          <Progress value={(currentStep / steps.length) * 100} className="h-2" />
          <CardDescription className="text-center mt-2">
            Step {currentStep} of {steps.length}
          </CardDescription>
        </CardHeader>
        <CardContent>{renderStepContent()}</CardContent>
      </Card>
    </div>
  );
};