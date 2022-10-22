## 結論
### mock
 - 全てのメソッドが一旦使用不可になる。
 - doReturnなどで戻り値を定義したメソッドだけ利用可能

### spy
 - 全てのメソッドはそのままで実行可能です。
 - doReturnなどで戻り値を定義したメソッドだけ戻り値が上書きされます。

## 使い分け
### mock
mockは特定の値を返してほしいときに使います。

### spy
spyは一部の振る舞いを変えたうえで他のクラスに食わせて、意図した振る舞いをさせるときに使います。  
例えば、Hoge.javaを持つことになる別のクラスに渡すとき、getB()の戻り値がNULLであることを期待するといった場合です。

## 例
### テスト対象

```java
package mock;

public class Hoge {

    public String getA() {
        return "A";
    }

    public String getB() {
        return "B";
    }

    public String getC() {
        return "C";
    }
}
```
### テストコード

```java
package mock;
 
import org.junit.jupiter.api.Test;
 
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;
import static org.mockito.Mockito.*;
 
class HogeTest {
 
    // getA()とgetC()はnullを返すのでコメントアウトしています。
    // getB()はdoReturnで指定した戻り値でテストが通ります。
    @Test
    public void testMockCase() {
        Hoge hoge = mock(Hoge.class);
        //assertThat("A", is(hoge.getA()));
        doReturn("BBB").when(hoge).getB();
        assertThat("BBB", is(hoge.getB()));
        //assertThat("C", is(hoge.getC()));
    }

    // getA()とgetC()はHoge.javaで定義されている元々の値を返します。
    // getB()はdoReturnで指定した戻り値でテストが通ります。
    @Test
    public void testSpyCase() {
        Hoge hoge = spy(Hoge.class);
        assertThat("A", is(hoge.getA()));
        doReturn("BBB").when(hoge).getB();
        assertThat("BBB", is(hoge.getB()));
        assertThat("C", is(hoge.getC()));
    }
}
```
