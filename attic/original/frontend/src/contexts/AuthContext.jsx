import { createContext, useContext, useState, useEffect } from 'react';
import {
  auth,
  googleProvider,
  facebookProvider,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  sendPasswordResetEmail,
  updateProfile
} from '../config/firebase';

const AuthContext = createContext(null);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('gramsahayak_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      if (firebaseUser) {
        const u = {
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName || 'Entrepreneur',
          photoURL: firebaseUser.photoURL,
          isGuest: false
        };
        setUser(u);
        localStorage.setItem('gramsahayak_user', JSON.stringify(u));
      } else if (!user?.isGuest) {
        setUser(null);
        localStorage.removeItem('gramsahayak_user');
      }
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const signup = async (email, password, displayName) => {
    const result = await createUserWithEmailAndPassword(auth, email, password);
    if (displayName) {
      await updateProfile(result.user, { displayName });
    }
    const u = {
      uid: result.user.uid,
      email: result.user.email,
      displayName: displayName || result.user.displayName || 'Entrepreneur',
      photoURL: result.user.photoURL,
      isGuest: false
    };
    setUser(u);
    localStorage.setItem('gramsahayak_user', JSON.stringify(u));
    return result;
  };

  const login = async (email, password) => {
    const result = await signInWithEmailAndPassword(auth, email, password);
    const u = {
      uid: result.user.uid,
      email: result.user.email,
      displayName: result.user.displayName || 'Entrepreneur',
      photoURL: result.user.photoURL,
      isGuest: false
    };
    setUser(u);
    localStorage.setItem('gramsahayak_user', JSON.stringify(u));
    return result;
  };

  const loginWithGoogle = async () => {
    const result = await signInWithPopup(auth, googleProvider);
    const u = {
      uid: result.user.uid,
      email: result.user.email,
      displayName: result.user.displayName || 'Entrepreneur',
      photoURL: result.user.photoURL,
      isGuest: false
    };
    setUser(u);
    localStorage.setItem('gramsahayak_user', JSON.stringify(u));
    return result;
  };

  const loginWithFacebook = async () => {
    const result = await signInWithPopup(auth, facebookProvider);
    const u = {
      uid: result.user.uid,
      email: result.user.email,
      displayName: result.user.displayName || 'Entrepreneur',
      photoURL: result.user.photoURL,
      isGuest: false
    };
    setUser(u);
    localStorage.setItem('gramsahayak_user', JSON.stringify(u));
    return result;
  };

  const loginAsDemo = (displayName = 'New Entrepreneur') => {
    const guestUser = {
      uid: `guest-${Date.now()}`,
      email: 'guest@gramsahayak.in',
      displayName,
      photoURL: null,
      isGuest: true
    };
    setUser(guestUser);
    localStorage.setItem('gramsahayak_user', JSON.stringify(guestUser));
    return guestUser;
  };

  const logout = async () => {
    setUser(null);
    localStorage.removeItem('gramsahayak_user');
    try {
      await signOut(auth);
    } catch {
      // Ignore firebase signOut errors in guest mode
    }
  };

  const resetPassword = (email) => {
    return sendPasswordResetEmail(auth, email);
  };

  const value = {
    user,
    loading,
    signup,
    login,
    loginAsDemo,
    loginWithGoogle,
    loginWithFacebook,
    logout,
    resetPassword,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthContext;
