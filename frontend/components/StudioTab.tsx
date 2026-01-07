'use client';

import { useState, useEffect } from 'react';
import { useStore } from '@/lib/store';
import { podcastAPI } from '@/lib/api-client';
import { getApiUrl } from '@/lib/env';
import { Mic, Loader2, Download } from 'lucide-react';

export default function StudioTab() {
  const { sources, setLoading, isLoading } = useStore();
  const [selectedSource, setSelectedSource] = useState('');
  const [podcastStyle, setPodcastStyle] = useState('Conversational');
  const [podcastLength, setPodcastLength] = useState('10 minutes');
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);
  const [successMessages, setSuccessMessages] = useState<string[]>([]);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (audioUrl && audioUrl.startsWith('blob:')) {
        window.URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const handleGenerate = async () => {
    if (!selectedSource) {
      setError('Please select a source');
      return;
    }

    setError('');
    setResult(null);
    setSuccessMessages([]);
    // Cleanup previous audio URL
    if (audioUrl && audioUrl.startsWith('blob:')) {
      window.URL.revokeObjectURL(audioUrl);
    }
    setAudioUrl(null);
    setLoading(true);

    try {
      const response = await podcastAPI.generatePodcast(selectedSource, podcastStyle, podcastLength);
      if (response.status && response.data) {
        console.log('Podcast generation response:', response.data);
        setResult(response.data);
        const messages: string[] = [];
        if (response.data.script_segments) {
          messages.push(`Generated podcast script with ${response.data.script_segments} dialogue segments!`);
        }
        if (response.data.audio_available && response.data.audio_file_count) {
          messages.push(`Generated ${response.data.audio_file_count} audio files!`);
        }
        setSuccessMessages(messages);
        
        // Load audio as blob for playback (required for auth headers)
        if (response.data.audio_available && response.data.audio_files && Array.isArray(response.data.audio_files) && response.data.audio_files.length > 0) {
          const audioApiUrl = `${getApiUrl()}${response.data.audio_files[0]}`;
          const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
          
          console.log('Loading audio from:', audioApiUrl);
          console.log('Audio files array:', response.data.audio_files);
          
          // Always fetch as blob since HTML5 audio doesn't support custom headers
          fetch(audioApiUrl, {
            headers: token ? {
              'Authorization': `Bearer ${token}`
            } : {}
          })
          .then(audioResponse => {
            console.log('Audio fetch response status:', audioResponse.status);
            if (!audioResponse.ok) {
              throw new Error(`Audio fetch failed: ${audioResponse.status} ${audioResponse.statusText}`);
            }
            return audioResponse.blob();
          })
          .then(blob => {
            console.log('Audio blob size:', blob.size, 'bytes');
            const blobUrl = window.URL.createObjectURL(blob);
            console.log('Audio loaded successfully, blob URL created:', blobUrl);
            setAudioUrl(blobUrl);
          })
          .catch(audioErr => {
            console.error('Failed to load audio:', audioErr);
            setError(`Failed to load audio: ${audioErr.message}. Please check the browser console for details.`);
            setAudioUrl(null);
          });
        } else {
          console.log('Audio not available:', {
            audio_available: response.data.audio_available,
            audio_files: response.data.audio_files,
            isArray: Array.isArray(response.data.audio_files),
            length: response.data.audio_files?.length
          });
          setAudioUrl(null);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate podcast');
      setSuccessMessages([]);
      setAudioUrl(null);
    } finally {
      setLoading(false);
    }
  };

  if (sources.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-400">
          <p className="text-lg mb-2">Studio output will be saved here.</p>
          <p>After adding sources, click to add Podcast Generation and more!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">🎙️ Generate Podcast</h2>
        <p className="text-gray-400">
          Create an AI-generated podcast discussion from your documents
        </p>
      </div>

      {error && (
        <div className="bg-primary/20 border border-primary/50 text-primary px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {successMessages.length > 0 && (
        <div className="space-y-2 mb-4">
          {successMessages.map((msg, idx) => (
            <div key={idx} className="bg-accent/20 border border-accent/50 text-accent px-4 py-3 rounded">
              {msg}
            </div>
          ))}
        </div>
      )}

      <div className="bg-secondary rounded-lg p-6 mb-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Select source for podcast</label>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Choose a document...</option>
              {sources.map((source, idx) => (
                <option key={idx} value={source.name}>
                  {source.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Podcast Style</label>
              <select
                value={podcastStyle}
                onChange={(e) => setPodcastStyle(e.target.value)}
                className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option>Conversational</option>
                <option>Interview</option>
                <option>Debate</option>
                <option>Educational</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Duration</label>
              <select
                value={podcastLength}
                onChange={(e) => setPodcastLength(e.target.value)}
                className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option>5 minutes</option>
                <option>10 minutes</option>
                <option>15 minutes</option>
                <option>20 minutes</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!selectedSource || isLoading}
            className="w-full px-6 py-3 bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
          >
            {isLoading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Generating Podcast...
              </>
            ) : (
              <>
                <Mic size={20} />
                Generate Podcast
              </>
            )}
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="bg-secondary rounded-lg p-6 mb-6">
          <div className="flex flex-col items-center justify-center gap-3 text-gray-400">
            <Loader2 size={24} className="animate-spin" />
            <div className="text-center">
              <p className="font-semibold">Generating podcast...</p>
              <p className="text-sm mt-1 text-gray-500">
                This may take a few minutes. Generating script and audio for all speakers...
              </p>
            </div>
          </div>
        </div>
      )}

      {result && (() => {
        let scriptData: any = null;
        try {
          scriptData = typeof result.script === 'string' ? JSON.parse(result.script) : result.script;
        } catch (e) {
          console.error('Failed to parse script:', e);
        }

        const scriptArray = scriptData?.script || [];
        const metadata = scriptData?.metadata || result.script_metadata || {};

        return (
          <div className="bg-secondary rounded-lg p-6">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <span>📝</span> Generated Podcast Script
            </h3>
            
            {/* Metrics */}
            <div className="mb-4 grid grid-cols-3 gap-4">
              <div className="bg-secondary-light p-3 rounded">
                <div className="text-sm text-gray-400 flex items-center gap-1">
                  <span>📊</span> Total Lines
                </div>
                <div className="text-lg font-semibold">{metadata.total_lines || scriptArray.length || 0}</div>
              </div>
              <div className="bg-secondary-light p-3 rounded">
                <div className="text-sm text-gray-400 flex items-center gap-1">
                  <span>⏱️</span> Est. Duration
                </div>
                <div className="text-lg font-semibold">{metadata.estimated_duration || result.script_metadata?.length || 'N/A'}</div>
              </div>
              <div className="bg-secondary-light p-3 rounded">
                <div className="text-sm text-gray-400 flex items-center gap-1">
                  <span>📄</span> Source Type
                </div>
                <div className="text-lg font-semibold">
                  {metadata.source_type || result.script_metadata?.source_type || 
                   (selectedSource.includes('.pdf') ? 'Document' : 
                    selectedSource.includes('http') ? 'Website' : 
                    selectedSource.includes('youtube') || selectedSource.includes('youtu.be') ? 'YouTube Video' : 
                    'Text')}
                </div>
              </div>
            </div>
            
            {/* Audio Section */}
            {result.audio_available ? (
              result.audio_files && Array.isArray(result.audio_files) && result.audio_files.length > 0 ? (
                <div className="mb-4">
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <Mic size={20} />
                    Generated Podcast
                  </h4>
                  <div className="bg-secondary-light p-4 rounded-lg">
                    {audioUrl ? (
                      <audio 
                        controls 
                        className="w-full mb-3"
                        style={{ 
                          width: '100%',
                          height: '54px'
                        }}
                      >
                        <source 
                          src={audioUrl} 
                          type="audio/wav" 
                        />
                        Your browser does not support the audio element.
                      </audio>
                    ) : (
                      <div className="mb-3 p-3 bg-secondary rounded flex items-center justify-center gap-2 text-gray-400">
                        <Loader2 size={20} className="animate-spin" />
                        <span>Loading audio...</span>
                      </div>
                    )}
                    <button
                      onClick={async () => {
                        try {
                          const audioApiUrl = `${getApiUrl()}${result.audio_files[0]}`;
                          const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
                          
                          const response = await fetch(audioApiUrl, {
                            headers: token ? {
                              'Authorization': `Bearer ${token}`
                            } : {}
                          });
                          
                          if (!response.ok) {
                            throw new Error('Failed to download audio');
                          }
                          
                          const blob = await response.blob();
                          const url = window.URL.createObjectURL(blob);
                          const link = document.createElement('a');
                          link.href = url;
                          link.download = 'complete_podcast.wav';
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                          window.URL.revokeObjectURL(url);
                        } catch (err) {
                          console.error('Download failed:', err);
                          alert('Failed to download podcast. Please try again.');
                        }
                      }}
                      className="w-full px-4 py-2 bg-primary hover:bg-primary-hover rounded-lg transition-colors flex items-center justify-center gap-2 font-semibold"
                    >
                      <Download size={18} />
                      Download Complete Podcast
                    </button>
                  </div>
                </div>
              ) : (
                <div className="mb-4 bg-secondary-light p-4 rounded-lg">
                  <p className="text-gray-400 text-center">
                    Audio files were not generated. Please check backend logs for details.
                  </p>
                </div>
              )
            ) : (
              <div className="mb-4 bg-secondary-light p-4 rounded-lg">
                <p className="text-gray-400 text-center">
                  Audio generation is not available.
                  <br />
                  <span className="text-sm mt-2 block">
                    {result.tts_error === "apex_conflict" ? (
                      <>
                        <span className="text-primary font-semibold">Package Conflict Detected:</span>
                        <br />
                        Coqui TTS requires NVIDIA apex library, but apex-saas-framework is installed, causing a conflict.
                        <br />
                        <span className="text-xs mt-2 block text-gray-500">
                          The podcast script was generated successfully. 
                          <br />
                          <span className="text-accent">Note: pyttsx3 fallback should be available. If you see this message, pyttsx3 may not be installed.</span>
                          <br />
                          Install pyttsx3: <code className="bg-secondary px-2 py-1 rounded">cd backend && uv add pyttsx3</code>
                        </span>
                      </>
                    ) : (
                      <>
                        TTS (Text-to-Speech) may not be installed or enabled.
                        <br />
                        <span className="text-xs mt-2 block">
                          To enable audio, install pyttsx3 (recommended): <code className="bg-secondary px-2 py-1 rounded">cd backend && uv add pyttsx3</code>
                          <br />
                          Or install Coqui TTS: <code className="bg-secondary px-2 py-1 rounded">pip install TTS{'>='}0.22.0</code>
                          <br />
                          If TTS is installed but not working, check backend logs for errors.
                        </span>
                      </>
                    )}
                  </span>
                </p>
              </div>
            )}

            {/* Script Display */}
            <div className="bg-secondary-light p-4 rounded">
              <div className="mb-2 flex items-center justify-between">
                <h4 className="font-semibold">View Complete Script</h4>
                <span className="text-gray-400">👁️👁️</span>
              </div>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {scriptArray.map((item: any, index: number) => {
                  const speaker = Object.keys(item)[0];
                  const dialogue = item[speaker];
                  const isSpeaker1 = speaker === 'Speaker 1';
                  
                  return (
                    <div
                      key={index}
                      className={`p-4 rounded-lg ${
                        isSpeaker1
                          ? 'bg-speaker1/30 border border-speaker1/60'
                          : 'bg-speaker2/30 border border-speaker2/60'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">
                          {isSpeaker1 ? '😊' : '😊'}
                        </span>
                        <div className="flex-1">
                          <div className="font-semibold mb-1 text-sm text-gray-300">
                            {speaker}
                          </div>
                          <div className="text-gray-100 leading-relaxed">
                            {dialogue}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

