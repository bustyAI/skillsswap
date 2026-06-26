"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import {
  getCurrentUser,
  getSession,
  signIn as cognitoSignIn,
  signUp as cognitoSignUp,
  confirmSignUp as cognitoConfirmSignUp,
  signOut as cognitoSignOut,
  resendConfirmationCode,
} from "@/lib/cognito";
import type { CognitoUserSession } from "amazon-cognito-identity-js";

interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  session: CognitoUserSession | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  confirmSignUp: (email: string, code: string) => Promise<void>;
  resendCode: (email: string) => Promise<void>;
  signOut: () => void;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<CognitoUserSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshSession = useCallback(async () => {
    try {
      const currentSession = await getSession();
      setSession(currentSession);
    } catch {
      setSession(null);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      const user = getCurrentUser();
      if (user) {
        await refreshSession();
      }
      setIsLoading(false);
    };
    init();
  }, [refreshSession]);

  const signIn = async (email: string, password: string) => {
    const newSession = await cognitoSignIn(email, password);
    setSession(newSession);
  };

  const signUp = async (email: string, password: string) => {
    await cognitoSignUp(email, password);
  };

  const confirmSignUp = async (email: string, code: string) => {
    await cognitoConfirmSignUp(email, code);
  };

  const resendCode = async (email: string) => {
    await resendConfirmationCode(email);
  };

  const signOut = () => {
    cognitoSignOut();
    setSession(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!session,
        isLoading,
        session,
        signIn,
        signUp,
        confirmSignUp,
        resendCode,
        signOut,
        refreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
