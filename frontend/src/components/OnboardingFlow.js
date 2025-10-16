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
    { name: 'Look Straight', duration: 8, instruction: 'Look directly at the camera, stay still' },
    { name: 'Look Up', duration: 8, instruction: 'Move your head and look up' },
    { name: 'Look Down', duration: 8, instruction: 'Move your head and look down' },
    { name: 'Look Left', duration: 8, instruction: 'Turn your head and look left' },
    { name: 'Look Right', duration: 8, instruction: 'Turn your head and look right' },
    { name: 'Smile', duration: 8, instruction: 'Smile naturally while looking at camera' },
    { name: 'Talk Naturally', duration: 30, instruction: 'Speak naturally - count 1 to 10 or say your name' }
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
    "The quick brown fox jumps over the lazy dog.",
    "Technology is amazing and constantly evolving.",
    "I enjoy learning new things every single day.",
    "One, two, three, four, five, six, seven, eight."
  ];
  
  // Step 4: Personality
  const [personality, setPersonality] = useState({
    formality: 5,
    enthusiasm: 5,
    verbosity: 5,
    humor: 5
  });

  // Video Recording Functions
  const handleStartVideoRecording = useCallback(() => {
    setRecordedChunks([]);
    setIsRecording(true);
    setRecordingTime(0);
    setCurrentExpression(0);
    
    const stream = webcamRef.current.stream;
    mediaRecorderRef.current = new MediaRecorder(stream, {
      mimeType: 'video/webm'
    });
    
    mediaRecorderRef.current.addEventListener('dataavailable', (event) => {
      if (event.data.size > 0) {
        setRecordedChunks((prev) => prev.concat(event.data));
      }
    });
    
    mediaRecorderRef.current.start();
    
    // Timer
    timerRef.current = setInterval(() => {
      setRecordingTime((prev) => {
        const newTime = prev + 1;
        
        // Auto-advance expressions
        let totalTime = 0;
        for (let i = 0; i < expressions.length; i++) {
          totalTime += expressions[i].duration;
          if (newTime <= totalTime) {
            setCurrentExpression(i);
            break;
          }
        }
        
        // Auto-stop after 78 seconds (total of all expressions)
        if (newTime >= 78) {
          handleStopVideoRecording();
        }
        
        return newTime;
      });
    }, 1000);
  }, [webcamRef]);
  
  const handleStopVideoRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
      
      // Create blob after recording stops
      setTimeout(() => {
        setRecordedChunks((chunks) => {
          if (chunks.length > 0) {
            const blob = new Blob(chunks, { type: 'video/webm' });
            setVideoBlob(blob);
            toast.success('Video recorded successfully!');
          }
          return chunks;
        });
      }, 100);
    }
  }, [isRecording]);
  
  const handleUploadVideo = async () => {
    if (!videoBlob) {
      toast.error('Please record a video first');
      return;
    }
    
    setLoading(true);
    try {
      const file = new File([videoBlob], 'avatar.webm', { type: 'video/webm' });
      await avatarAPI.upload(file);
      toast.success('Video uploaded! Training started...');
      nextStep();
    } catch (error) {
      toast.error('Failed to upload video');
    } finally {
      setLoading(false);
    }
  };
  
  // Voice Recording Functions
  const handleStartVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioRecorderRef.current = new MediaRecorder(stream);
      const chunks = [];
      
      audioRecorderRef.current.addEventListener('dataavailable', (event) => {
        chunks.push(event.data);
      });
      
      audioRecorderRef.current.addEventListener('stop', () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setVoiceBlob(blob);
        stream.getTracks().forEach(track => track.stop());
        toast.success('Voice recorded successfully!');
      });
      
      audioRecorderRef.current.start();
      setIsRecordingVoice(true);
      setVoiceRecordingTime(0);
      setCurrentTextIndex(0);
      
      // Timer
      voiceTimerRef.current = setInterval(() => {
        setVoiceRecordingTime((prev) => {
          const newTime = prev + 1;
          
          // Auto-advance text every 8 seconds
          if (newTime % 8 === 0 && currentTextIndex < readingTexts.length - 1) {
            setCurrentTextIndex(prev => prev + 1);
          }
          
          // Auto-stop after 50 seconds (5 texts * 8 seconds + 10s buffer)
          if (newTime >= 50) {
            handleStopVoiceRecording();
          }
          
          return newTime;
        });
      }, 1000);
    } catch (error) {
      toast.error('Failed to access microphone');
    }
  };
  
  const handleStopVoiceRecording = () => {
    if (audioRecorderRef.current && isRecordingVoice) {
      audioRecorderRef.current.stop();
      setIsRecordingVoice(false);
      clearInterval(voiceTimerRef.current);
    }
  };
  
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

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
    await handleUploadVideo();
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
              <h3 className="text-2xl font-bold">Record Your Avatar Video</h3>
              <p className="text-muted-foreground">
                Follow the on-screen instructions for ~78 seconds
              </p>
            </div>
            
            {!videoBlob ? (
              <div className="space-y-4">
                <div className="relative rounded-lg overflow-hidden bg-black aspect-video">
                  <Webcam
                    ref={webcamRef}
                    audio={false}
                    className="w-full h-full object-cover"
                    mirrored
                  />
                  
                  {isRecording && (
                    <div className="absolute top-4 left-4 right-4">
                      <div className="bg-black/80 backdrop-blur-sm rounded-lg p-4 text-white">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <Circle className="h-3 w-3 text-red-500 fill-red-500 animate-pulse" />
                            <span className="text-sm font-medium">Recording</span>
                          </div>
                          <span className="text-xl font-mono">{formatTime(recordingTime)}</span>
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm opacity-80">Step {currentExpression + 1}/7</span>
                            <span className="text-lg font-bold text-primary">{expressions[currentExpression].name}</span>
                          </div>
                          <div className="bg-white/10 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold mb-1">
                              {expressions[currentExpression].instruction}
                            </div>
                            <div className="text-sm opacity-75">
                              {(() => {
                                let elapsed = 0;
                                for (let i = 0; i < currentExpression; i++) {
                                  elapsed += expressions[i].duration;
                                }
                                const remaining = expressions[currentExpression].duration - (recordingTime - elapsed);
                                return `${remaining}s remaining`;
                              })()}
                            </div>
                          </div>
                          <Progress 
                            value={(recordingTime / 78) * 100} 
                            className="h-2"
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2">
                  {!isRecording ? (
                    <Button
                      onClick={handleStartVideoRecording}
                      className="flex-1"
                      data-testid="start-video-recording-button"
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Start Recording
                    </Button>
                  ) : (
                    <Button
                      onClick={handleStopVideoRecording}
                      variant="destructive"
                      className="flex-1"
                      data-testid="stop-video-recording-button"
                    >
                      <Square className="h-4 w-4 mr-2" />
                      Stop Recording
                    </Button>
                  )}
                </div>
                
                <div className="bg-muted rounded-lg p-4 text-sm">
                  <h4 className="font-medium mb-2">Recording Instructions (78 seconds):</h4>
                  <div className="grid grid-cols-2 gap-2 text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-primary">1.</span>
                      <span>Look Straight (8s)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-primary">2.</span>
                      <span>Look Up (8s)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-primary">3.</span>
                      <span>Look Down (8s)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-primary">4.</span>
                      <span>Look Left (8s)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-primary">5.</span>
                      <span>Look Right (8s)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-primary">6.</span>
                      <span>Smile (8s)</span>
                    </div>
                    <div className="flex items-center gap-2 col-span-2">
                      <span className="font-bold text-primary">7.</span>
                      <span>Talk Naturally - Count 1-10 (30s)</span>
                    </div>
                  </div>
                  <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-900">
                    💡 <strong>Tip:</strong> Keep your face clearly visible and follow each instruction as it appears
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="relative rounded-lg overflow-hidden bg-black aspect-video">
                  <video
                    src={URL.createObjectURL(videoBlob)}
                    controls
                    className="w-full h-full"
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setVideoBlob(null);
                      setRecordedChunks([]);
                    }}
                    className="flex-1"
                  >
                    Re-record
                  </Button>
                  <Button
                    onClick={handleVideoUpload}
                    disabled={loading}
                    className="flex-1"
                    data-testid="upload-video-button"
                  >
                    {loading ? 'Uploading...' : 'Upload & Continue'}
                  </Button>
                </div>
              </div>
            )}
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={prevStep} className="flex-1">
                Back
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
                Read 5 sentences clearly (~50 seconds)
              </p>
            </div>
            
            {!voiceBlob ? (
              <div className="space-y-4">
                <div className="bg-muted rounded-lg p-6">
                  <div className="text-center mb-4">
                    {isRecordingVoice ? (
                      <div className="space-y-3">
                        <div className="flex items-center justify-center gap-2">
                          <Circle className="h-4 w-4 text-red-500 fill-red-500 animate-pulse" />
                          <span className="text-lg font-medium">Recording...</span>
                        </div>
                        <div className="text-3xl font-mono">{formatTime(voiceRecordingTime)}</div>
                        <Progress value={(voiceRecordingTime / 50) * 100} className="h-2" />
                      </div>
                    ) : (
                      <div className="text-muted-foreground">
                        Press start to begin recording
                      </div>
                    )}
                  </div>
                  
                  {isRecordingVoice && (
                    <div className="bg-background rounded-lg p-4 mt-4">
                      <div className="text-xs text-muted-foreground mb-2">
                        Text {currentTextIndex + 1} of {readingTexts.length}
                      </div>
                      <p className="text-lg text-center font-medium">
                        "{readingTexts[currentTextIndex]}"
                      </p>
                    </div>
                  )}
                </div>
                
                <div className="bg-muted rounded-lg p-4">
                  <h4 className="font-medium mb-2 text-sm">Preview Texts:</h4>
                  <div className="space-y-1 text-xs text-muted-foreground max-h-32 overflow-y-auto">
                    {readingTexts.slice(0, 5).map((text, idx) => (
                      <p key={idx}>• {text}</p>
                    ))}
                    <p className="text-xs opacity-60">...and {readingTexts.length - 5} more</p>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  {!isRecordingVoice ? (
                    <Button
                      onClick={handleStartVoiceRecording}
                      className="flex-1"
                      data-testid="start-voice-recording-button"
                    >
                      <Mic className="h-4 w-4 mr-2" />
                      Start Recording
                    </Button>
                  ) : (
                    <Button
                      onClick={handleStopVoiceRecording}
                      variant="destructive"
                      className="flex-1"
                      data-testid="stop-voice-recording-button"
                    >
                      <Square className="h-4 w-4 mr-2" />
                      Stop Recording
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                  <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-500" />
                  <p className="font-medium text-green-900">Voice recorded successfully!</p>
                  <p className="text-sm text-green-700 mt-1">
                    Duration: {formatTime(voiceRecordingTime)}
                  </p>
                </div>
                
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setVoiceBlob(null);
                      setVoiceRecordingTime(0);
                      setCurrentTextIndex(0);
                    }}
                    className="flex-1"
                  >
                    Re-record
                  </Button>
                  <Button 
                    onClick={nextStep} 
                    className="flex-1"
                    data-testid="step-3-next-button"
                  >
                    Continue
                  </Button>
                </div>
              </div>
            )}
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={prevStep} className="flex-1">
                Back
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