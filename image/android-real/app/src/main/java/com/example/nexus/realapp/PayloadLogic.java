package com.example.nexus.realapp;

/** Pure Java logic included in the APK DEX and also exercised by a local JVM smoke. */
public final class PayloadLogic {
    private PayloadLogic() {}

    public static int calculate(int left, int right) {
        return left * right;
    }

    public static void main(String[] args) {
        int result = calculate(6, 7);
        System.out.println("JVM Java bytecode executed: 6 x 7 = " + result);
        if (result != 42) System.exit(1);
    }
}
