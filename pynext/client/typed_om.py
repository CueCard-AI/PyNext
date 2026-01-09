"""
PyNext Client - CSS Typed Object Model

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides Python type stubs for CSS Typed OM (CSS Houdini) APIs, enabling
type-safe CSS value manipulation with proper IDE autocompletion.

=============================================================================
WHY THIS EXISTS
=============================================================================

Traditional CSS manipulation uses strings:
    el.style.width = "100px"  # No type safety, easy to make mistakes

CSS Typed OM provides typed values:
    el.attributeStyleMap.set("width", CSS.px(100))  # Type-safe!

Benefits:
- Type-safe CSS values with IDE autocompletion
- Arithmetic operations on CSS values (add, subtract, multiply)
- Unit conversion (px to em, deg to rad, etc.)
- Better performance (browser doesn't need to parse strings)

=============================================================================
HOW IT WORKS
=============================================================================

All CSS Typed OM calls are **passthrough** - they transpile 1:1 to JavaScript:

    Python:  CSS.px(100)
    JS:      CSS.px(100)

    Python:  el.attributeStyleMap.set("width", CSS.px(100))
    JS:      el.attributeStyleMap.set("width", CSS.px(100))

The browser's native CSS Typed OM API handles everything at runtime.

=============================================================================
WHO USES THIS
=============================================================================

- Developers wanting type-safe CSS manipulation
- Applications requiring CSS value arithmetic
- Dynamic styling systems with computed values
- Animation systems with precise control

=============================================================================
BROWSER SUPPORT
=============================================================================

CSS Typed OM is part of CSS Houdini:
- Chrome/Edge: Full support (since Chrome 66)
- Safari: Partial support (since Safari 16.4)
- Firefox: Limited support

For wider compatibility, use traditional element.style with string values.

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client import CSS, CSSUnitValue
    
    # Create typed values
    width = CSS.px(100)           # CSSUnitValue: 100px
    height = CSS.percent(50)      # CSSUnitValue: 50%
    angle = CSS.deg(45)           # CSSUnitValue: 45deg
    
    # Arithmetic
    doubled = width.mul(2)        # 200px
    half = height.div(2)          # 25%
    
    # Access components
    print(width.value)            # 100
    print(width.unit)             # "px"
    
    # Apply to element
    el.attributeStyleMap.set("width", CSS.px(200))
    
    # Math functions
    width = CSS.calc("100% - 20px")
    min_width = CSS.min(CSS.px(100), CSS.percent(50))
"""

from __future__ import annotations
from typing import (
    Any,
    Iterator,
    List,
    Optional,
    Union,
    overload,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from pynext.client.dom import Element


# =============================================================================
# Base CSS Value Types
# =============================================================================

class CSSStyleValue:
    """
    WHO: Base class for all CSS typed values
    WHAT: Abstract base for CSSUnitValue, CSSKeywordValue, etc.
    WHEN: Used as type hint for any CSS value
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Polymorphic CSS value handling
    HOW: Zero-runtime passthrough
    
    This is the base class - you typically use specific subclasses:
    - CSSUnitValue for numeric values with units
    - CSSKeywordValue for keyword values like "auto"
    - CSSMathValue for calc(), min(), max(), etc.
    """
    
    def toString(self) -> str:
        """
        Convert to CSS string representation.
        
        Returns:
            CSS string like "100px", "50%", "auto"
        """
        ...
    
    def __str__(self) -> str:
        """Python string conversion."""
        ...


class CSSNumericValue(CSSStyleValue):
    """
    WHO: Base for numeric CSS values
    WHAT: Abstract base for values that support arithmetic
    WHEN: Used for CSS values with numeric components
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Enable arithmetic operations on CSS values
    HOW: Zero-runtime passthrough
    """
    
    def add(self, *values: CSSNumericValue) -> CSSNumericValue:
        """
        Add numeric values.
        
        Args:
            values: Values to add
        
        Returns:
            Sum as CSSMathSum or simplified CSSUnitValue
        
        Example:
            total = CSS.px(100).add(CSS.px(50))  # 150px
        """
        ...
    
    def sub(self, *values: CSSNumericValue) -> CSSNumericValue:
        """
        Subtract numeric values.
        
        Args:
            values: Values to subtract
        
        Returns:
            Difference as CSSMathSum or simplified CSSUnitValue
        
        Example:
            diff = CSS.px(100).sub(CSS.px(30))  # 70px
        """
        ...
    
    def mul(self, *values: Union[float, CSSNumericValue]) -> CSSNumericValue:
        """
        Multiply by factor(s).
        
        Args:
            values: Multipliers (numbers or CSS values)
        
        Returns:
            Product as CSSMathProduct or simplified CSSUnitValue
        
        Example:
            doubled = CSS.px(100).mul(2)  # 200px
        """
        ...
    
    def div(self, *values: Union[float, CSSNumericValue]) -> CSSNumericValue:
        """
        Divide by factor(s).
        
        Args:
            values: Divisors (numbers or CSS values)
        
        Returns:
            Quotient as CSSMathProduct or simplified CSSUnitValue
        
        Example:
            half = CSS.px(100).div(2)  # 50px
        """
        ...
    
    def min(self, *values: CSSNumericValue) -> CSSNumericValue:
        """
        Get minimum of values.
        
        Args:
            values: Values to compare
        
        Returns:
            CSSMathMin containing all values
        """
        ...
    
    def max(self, *values: CSSNumericValue) -> CSSNumericValue:
        """
        Get maximum of values.
        
        Args:
            values: Values to compare
        
        Returns:
            CSSMathMax containing all values
        """
        ...
    
    def equals(self, *values: CSSNumericValue) -> bool:
        """
        Check equality with other values.
        
        Args:
            values: Values to compare
        
        Returns:
            True if all values are equal
        
        Example:
            CSS.px(100).equals(CSS.px(100))  # True
        """
        ...
    
    def to(self, unit: str) -> CSSUnitValue:
        """
        Convert to a different unit.
        
        Args:
            unit: Target unit ("px", "em", "deg", etc.)
        
        Returns:
            Converted CSSUnitValue
        
        Raises:
            TypeError: If conversion is not possible
        
        Example:
            radians = CSS.deg(180).to("rad")  # ~3.14159rad
        """
        ...
    
    def toSum(self, *units: str) -> CSSMathSum:
        """
        Express value as sum of specified units.
        
        Args:
            units: Units to express the value in
        
        Returns:
            CSSMathSum in specified units
        """
        ...
    
    def type(self) -> CSSNumericType:
        """
        Get the numeric type of this value.
        
        Returns:
            CSSNumericType describing the dimensions
        """
        ...


# =============================================================================
# CSSUnitValue - Core Numeric Value with Unit
# =============================================================================

class CSSUnitValue(CSSNumericValue):
    """
    WHO: Developers working with CSS values that have units
    WHAT: A numeric CSS value with a unit (100px, 50%, 45deg)
    WHEN: Use for any CSS property requiring a value with unit
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe, arithmetic-capable CSS values
    HOW: Zero-runtime passthrough to browser's CSSUnitValue
    
    Properties:
        value: The numeric value (float)
        unit: The unit string ("px", "%", "em", etc.)
    
    Transpilation:
        Python: CSS.px(100)
        JS:     CSS.px(100)
    
    Example:
        width = CSS.px(100)
        print(width.value)  # 100
        print(width.unit)   # "px"
        
        doubled = width.mul(2)  # 200px
        half = width.div(2)     # 50px
    """
    
    def __init__(self, value: float, unit: str) -> None:
        """
        Create a CSSUnitValue directly.
        
        Prefer using CSS factory methods (CSS.px, CSS.percent, etc.)
        for cleaner code.
        
        Args:
            value: Numeric value
            unit: Unit string
        
        Example:
            # Prefer this:
            width = CSS.px(100)
            
            # Over this:
            width = CSSUnitValue(100, "px")
        """
        ...
    
    @property
    def value(self) -> float:
        """
        The numeric value.
        
        Example:
            CSS.px(100).value  # 100
            CSS.percent(50).value  # 50
        """
        ...
    
    @value.setter
    def value(self, v: float) -> None:
        """Set the numeric value."""
        ...
    
    @property
    def unit(self) -> str:
        """
        The unit string.
        
        Example:
            CSS.px(100).unit  # "px"
            CSS.percent(50).unit  # "percent"
            CSS.deg(45).unit  # "deg"
        """
        ...
    
    @unit.setter
    def unit(self, u: str) -> None:
        """Set the unit."""
        ...


# =============================================================================
# CSSKeywordValue - CSS Keywords
# =============================================================================

class CSSKeywordValue(CSSStyleValue):
    """
    WHO: Developers using CSS keyword values
    WHAT: A CSS keyword value like "auto", "inherit", "none"
    WHEN: Use for CSS properties that accept keywords
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe keyword handling
    HOW: Zero-runtime passthrough
    
    Example:
        auto = CSS.keyword("auto")
        el.attributeStyleMap.set("width", auto)
        
        # Or directly:
        el.attributeStyleMap.set("display", CSS.keyword("flex"))
    """
    
    def __init__(self, value: str) -> None:
        """
        Create a CSSKeywordValue.
        
        Args:
            value: The keyword string
        """
        ...
    
    @property
    def value(self) -> str:
        """The keyword string."""
        ...
    
    @value.setter
    def value(self, v: str) -> None:
        """Set the keyword."""
        ...


class CSSUnparsedValue(CSSStyleValue):
    """
    WHO: Developers working with CSS custom properties (variables)
    WHAT: Represents an unparsed CSS value containing var() references
    WHEN: Returned when getting custom properties from StylePropertyMap
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Custom properties may contain var() and can't be fully parsed
    HOW: Zero-runtime passthrough
    
    Example:
        # Custom properties return CSSUnparsedValue
        custom = el.computedStyleMap().get("--my-spacing")
        
        # Iterate over tokens
        for token in custom:
            print(token)  # String or CSSVariableReferenceValue
    """
    
    @property
    def length(self) -> int:
        """Number of tokens in the unparsed value."""
        ...
    
    def __getitem__(self, index: int) -> Union[str, 'CSSVariableReferenceValue']:
        """Get token at index."""
        ...
    
    def __iter__(self) -> Iterator[Union[str, 'CSSVariableReferenceValue']]:
        """Iterate over tokens."""
        ...
    
    def __len__(self) -> int:
        """Number of tokens."""
        ...


class CSSVariableReferenceValue:
    """
    Represents a var() reference within a CSSUnparsedValue.
    
    Example:
        # In a custom property like "--derived: calc(var(--base) + 10px)"
        # The var(--base) part is a CSSVariableReferenceValue
    """
    
    @property
    def variable(self) -> str:
        """The variable name (without --)."""
        ...
    
    @property
    def fallback(self) -> Optional[CSSUnparsedValue]:
        """The fallback value, if any."""
        ...


# =============================================================================
# CSS Math Values (calc, min, max, clamp)
# =============================================================================

class CSSMathValue(CSSNumericValue):
    """
    WHO: Base for CSS math function values
    WHAT: Abstract base for calc(), min(), max(), clamp() results
    WHEN: Used when CSS values involve calculations
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Represent complex CSS calculations
    HOW: Zero-runtime passthrough
    """
    
    @property
    def operator(self) -> str:
        """
        The math operator.
        
        Values: "sum", "product", "negate", "invert", "min", "max", "clamp"
        """
        ...


class CSSMathSum(CSSMathValue):
    """
    WHO: Developers working with CSS addition/subtraction
    WHAT: Represents a sum of CSS values (result of add/sub or calc)
    WHEN: Created by add(), sub(), or calc() with + or -
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Represent CSS sums like calc(100% - 20px)
    HOW: Zero-runtime passthrough
    
    Example:
        # From arithmetic
        sum_val = CSS.percent(100).sub(CSS.px(20))
        
        # From calc
        sum_val = CSS.calc("100% - 20px")
    """
    
    @property
    def values(self) -> List[CSSNumericValue]:
        """The values being summed."""
        ...


class CSSMathProduct(CSSMathValue):
    """
    WHO: Developers working with CSS multiplication/division
    WHAT: Represents a product of CSS values
    WHEN: Created by mul(), div(), or calc() with * or /
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Represent CSS products
    HOW: Zero-runtime passthrough
    """
    
    @property
    def values(self) -> List[CSSNumericValue]:
        """The values being multiplied."""
        ...


class CSSMathNegate(CSSMathValue):
    """Represents negation of a CSS value."""
    
    @property
    def value(self) -> CSSNumericValue:
        """The negated value."""
        ...


class CSSMathInvert(CSSMathValue):
    """Represents inversion (1/x) of a CSS value."""
    
    @property
    def value(self) -> CSSNumericValue:
        """The inverted value."""
        ...


class CSSMathMin(CSSMathValue):
    """
    WHO: Developers using CSS min() function
    WHAT: Represents min() of CSS values
    WHEN: Created by CSS.min() or min()
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe min() representation
    HOW: Zero-runtime passthrough
    
    Example:
        min_val = CSS.min(CSS.px(100), CSS.percent(50))
    """
    
    @property
    def values(self) -> List[CSSNumericValue]:
        """The values to find minimum of."""
        ...


class CSSMathMax(CSSMathValue):
    """
    WHO: Developers using CSS max() function
    WHAT: Represents max() of CSS values
    WHEN: Created by CSS.max() or max()
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe max() representation
    HOW: Zero-runtime passthrough
    """
    
    @property
    def values(self) -> List[CSSNumericValue]:
        """The values to find maximum of."""
        ...


class CSSMathClamp(CSSMathValue):
    """
    WHO: Developers using CSS clamp() function
    WHAT: Represents clamp(min, val, max)
    WHEN: Created by CSS.clamp()
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe clamp() representation
    HOW: Zero-runtime passthrough
    
    Example:
        clamped = CSS.clamp(CSS.px(100), CSS.percent(50), CSS.px(300))
    """
    
    @property
    def min(self) -> CSSNumericValue:
        """The minimum value."""
        ...
    
    @property
    def val(self) -> CSSNumericValue:
        """The preferred value."""
        ...
    
    @property
    def max(self) -> CSSNumericValue:
        """The maximum value."""
        ...


class CSSNumericType:
    """Describes the type/dimensions of a CSS numeric value."""
    
    length: int
    angle: int
    time: int
    frequency: int
    resolution: int
    flex: int
    percent: int
    percentHint: str


# =============================================================================
# CSS Transform Values
# =============================================================================

class CSSTransformValue(CSSStyleValue):
    """
    WHO: Developers working with CSS transforms
    WHAT: A list of transform components
    WHEN: Use for complex transforms combining multiple operations
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe transform manipulation
    HOW: Zero-runtime passthrough
    
    Example:
        transform = CSSTransformValue([
            CSS.translate(CSS.px(100), CSS.px(50)),
            CSS.rotate(CSS.deg(45)),
            CSS.scale(2),
        ])
        el.attributeStyleMap.set("transform", transform)
    """
    
    def __init__(self, transforms: List[CSSTransformComponent]) -> None:
        """
        Create a CSSTransformValue from components.
        
        Args:
            transforms: List of transform components
        """
        ...
    
    @property
    def length(self) -> int:
        """Number of transform components."""
        ...
    
    def __getitem__(self, index: int) -> CSSTransformComponent:
        """Get transform component by index."""
        ...
    
    def __setitem__(self, index: int, value: CSSTransformComponent) -> None:
        """Set transform component at index."""
        ...
    
    def __iter__(self) -> Iterator[CSSTransformComponent]:
        """Iterate over transform components."""
        ...
    
    @property
    def is2D(self) -> bool:
        """True if all components are 2D."""
        ...
    
    def toMatrix(self) -> DOMMatrix:
        """
        Convert to a DOMMatrix.
        
        Returns:
            DOMMatrix representing the combined transform
        """
        ...


class CSSTransformComponent:
    """Base class for transform components."""
    
    @property
    def is2D(self) -> bool:
        """True if this is a 2D transform."""
        ...
    
    def toMatrix(self) -> DOMMatrix:
        """Convert to DOMMatrix."""
        ...


class CSSTranslate(CSSTransformComponent):
    """translate() transform component."""
    
    def __init__(
        self,
        x: CSSNumericValue,
        y: CSSNumericValue,
        z: Optional[CSSNumericValue] = None
    ) -> None:
        ...
    
    x: CSSNumericValue
    y: CSSNumericValue
    z: CSSNumericValue


class CSSRotate(CSSTransformComponent):
    """rotate() transform component."""
    
    def __init__(
        self,
        angle: CSSNumericValue,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None
    ) -> None:
        ...
    
    angle: CSSNumericValue
    x: float
    y: float
    z: float


class CSSScale(CSSTransformComponent):
    """scale() transform component."""
    
    def __init__(
        self,
        x: float,
        y: Optional[float] = None,
        z: Optional[float] = None
    ) -> None:
        ...
    
    x: float
    y: float
    z: float


class CSSSkew(CSSTransformComponent):
    """skew() transform component."""
    
    def __init__(
        self,
        ax: CSSNumericValue,
        ay: Optional[CSSNumericValue] = None
    ) -> None:
        ...
    
    ax: CSSNumericValue
    ay: CSSNumericValue


class CSSSkewX(CSSTransformComponent):
    """skewX() transform component."""
    
    def __init__(self, ax: CSSNumericValue) -> None:
        ...
    
    ax: CSSNumericValue


class CSSSkewY(CSSTransformComponent):
    """skewY() transform component."""
    
    def __init__(self, ay: CSSNumericValue) -> None:
        ...
    
    ay: CSSNumericValue


class CSSPerspective(CSSTransformComponent):
    """perspective() transform component."""
    
    def __init__(self, length: CSSNumericValue) -> None:
        ...
    
    length: CSSNumericValue


class CSSMatrixComponent(CSSTransformComponent):
    """matrix() or matrix3d() transform component."""
    
    def __init__(self, matrix: DOMMatrix, options: Optional[dict] = None) -> None:
        ...
    
    matrix: DOMMatrix


class DOMMatrix:
    """4x4 transformation matrix (stub for transforms)."""
    
    # 2D matrix components
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float
    
    # 3D matrix components (m11-m44)
    m11: float
    m12: float
    m13: float
    m14: float
    m21: float
    m22: float
    m23: float
    m24: float
    m31: float
    m32: float
    m33: float
    m34: float
    m41: float
    m42: float
    m43: float
    m44: float
    
    is2D: bool
    isIdentity: bool
    
    def multiply(self, other: DOMMatrix) -> DOMMatrix: ...
    def translate(self, tx: float, ty: float, tz: float = 0) -> DOMMatrix: ...
    def scale(self, sx: float, sy: float = ..., sz: float = 1) -> DOMMatrix: ...
    def rotate(self, rx: float, ry: float = 0, rz: float = 0) -> DOMMatrix: ...
    def inverse(self) -> DOMMatrix: ...
    def transformPoint(self, point: dict) -> dict: ...


# =============================================================================
# CSS Image Values (for backgrounds, etc.)
# =============================================================================

class CSSImageValue(CSSStyleValue):
    """
    Represents a CSS image value (url, gradient, etc.).
    
    WHO: Developers working with CSS background images
    WHAT: Type-safe representation of CSS image values
    WHEN: Use for typed background-image manipulation
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type safety for image-based CSS properties
    HOW: Zero-runtime passthrough to browser API
    
    Note: CSSImageValue is read-only in most browsers.
    Use CSS.url() or gradient constructors to create images.
    
    Example:
        # Currently, images are typically set via style strings
        el.style.backgroundImage = "url('/image.png')"
        
        # With CSSImageValue (future full support)
        el.attributeStyleMap.set("background-image", CSS.url("/image.png"))
    """
    
    @property
    def intrinsicWidth(self) -> Optional[float]:
        """Intrinsic width of the image, if known."""
        ...
    
    @property
    def intrinsicHeight(self) -> Optional[float]:
        """Intrinsic height of the image, if known."""
        ...
    
    @property
    def intrinsicRatio(self) -> Optional[float]:
        """Intrinsic aspect ratio (width/height), if known."""
        ...


class CSSURLImageValue(CSSImageValue):
    """
    Represents a url() image value.
    
    Example:
        img = CSS.url("/path/to/image.png")
        el.attributeStyleMap.set("background-image", img)
    """
    
    @property
    def url(self) -> str:
        """The URL string."""
        ...


class CSSLinearGradient(CSSImageValue):
    """
    Represents a linear-gradient() value.
    
    Example:
        gradient = CSS.linearGradient("to right", ["red", "blue"])
        el.attributeStyleMap.set("background", gradient)
    """
    pass


class CSSRadialGradient(CSSImageValue):
    """
    Represents a radial-gradient() value.
    
    Example:
        gradient = CSS.radialGradient("circle", ["red", "blue"])
        el.attributeStyleMap.set("background", gradient)
    """
    pass


class CSSConicGradient(CSSImageValue):
    """
    Represents a conic-gradient() value.
    
    Example:
        gradient = CSS.conicGradient("from 0deg", ["red", "blue", "red"])
        el.attributeStyleMap.set("background", gradient)
    """
    pass


# =============================================================================
# StylePropertyMap - Typed Style Manipulation
# =============================================================================

class StylePropertyMapReadOnly:
    """
    WHO: Developers reading CSS properties with typed values
    WHAT: Read-only map of CSS property names to typed values
    WHEN: Use for reading computed styles
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe CSS property access
    HOW: Zero-runtime passthrough
    
    Accessed via: el.computedStyleMap()
    """
    
    def get(self, property: str) -> Optional[CSSStyleValue]:
        """
        Get the first value for a property.
        
        Args:
            property: CSS property name (e.g., "width", "background-color")
        
        Returns:
            The CSSStyleValue, or None if not set
        
        Example:
            width = el.computedStyleMap().get("width")
            if width:
                print(width.value, width.unit)  # 100 "px"
        """
        ...
    
    def getAll(self, property: str) -> List[CSSStyleValue]:
        """
        Get all values for a property (for shorthand expansion).
        
        Args:
            property: CSS property name
        
        Returns:
            List of CSSStyleValue objects
        """
        ...
    
    def has(self, property: str) -> bool:
        """
        Check if property has a value.
        
        Args:
            property: CSS property name
        
        Returns:
            True if property has a value
        """
        ...
    
    def keys(self) -> Iterator[str]:
        """
        Iterate over property names.
        
        Yields:
            Property names
        """
        ...
    
    def values(self) -> Iterator[CSSStyleValue]:
        """
        Iterate over values.
        
        Yields:
            CSSStyleValue objects
        """
        ...
    
    def entries(self) -> Iterator[tuple[str, CSSStyleValue]]:
        """
        Iterate over (property, value) pairs.
        
        Yields:
            Tuples of (property_name, value)
        """
        ...
    
    def forEach(
        self,
        callback: Any,
        thisArg: Optional[Any] = None
    ) -> None:
        """Call callback for each property."""
        ...
    
    @property
    def size(self) -> int:
        """Number of properties."""
        ...


class StylePropertyMap(StylePropertyMapReadOnly):
    """
    WHO: Developers manipulating CSS properties with typed values
    WHAT: Mutable map of CSS property names to typed values
    WHEN: Use for setting inline styles with type safety
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe, performant CSS property manipulation
    HOW: Zero-runtime passthrough
    
    Accessed via: el.attributeStyleMap
    
    Example:
        style_map = el.attributeStyleMap
        style_map.set("width", CSS.px(100))
        style_map.set("height", CSS.percent(50))
        style_map.set("transform", CSSTransformValue([
            CSS.rotate(CSS.deg(45)),
        ]))
        
        width = style_map.get("width")
        print(width.value)  # 100
        
        style_map.delete("height")
        style_map.clear()
    """
    
    def set(self, property: str, value: CSSStyleValue) -> None:
        """
        Set a property value.
        
        Args:
            property: CSS property name
            value: CSSStyleValue to set
        
        Example:
            el.attributeStyleMap.set("width", CSS.px(100))
            el.attributeStyleMap.set("display", CSS.keyword("flex"))
        """
        ...
    
    def append(self, property: str, value: CSSStyleValue) -> None:
        """
        Append a value to a property (for multi-value properties).
        
        Args:
            property: CSS property name
            value: CSSStyleValue to append
        """
        ...
    
    def delete(self, property: str) -> None:
        """
        Delete a property.
        
        Args:
            property: CSS property name to remove
        
        Example:
            el.attributeStyleMap.delete("width")
        """
        ...
    
    def clear(self) -> None:
        """
        Clear all properties.
        
        Example:
            el.attributeStyleMap.clear()
        """
        ...


# =============================================================================
# CSS Factory Namespace
# =============================================================================

class CSS:
    """
    WHO: Developers creating type-safe CSS values
    WHAT: Factory methods for all CSS unit types
    WHEN: Use instead of string CSS values for type safety and arithmetic
    WHERE: Client-side code (transpiles to browser CSS namespace)
    WHY: Type-safe, performant CSS value creation
    HOW: Zero-runtime passthrough to browser's CSS global
    
    All methods transpile 1:1:
        Python: CSS.px(100)
        JS:     CSS.px(100)
    
    Example:
        from pynext.client import CSS
        
        # Length units
        width = CSS.px(100)
        height = CSS.percent(50)
        margin = CSS.rem(2)
        
        # Angle units
        rotation = CSS.deg(45)
        
        # Time units
        duration = CSS.ms(300)
        
        # Math functions
        calc_width = CSS.calc("100% - 20px")
        min_height = CSS.min(CSS.px(200), CSS.vh(50))
        clamped = CSS.clamp(CSS.px(100), CSS.percent(50), CSS.px(400))
        
        # Apply to element
        el.attributeStyleMap.set("width", width)
    """
    
    # =========================================================================
    # Length Units
    # =========================================================================
    
    @staticmethod
    def px(value: float) -> CSSUnitValue:
        """
        Create a pixel value.
        
        Args:
            value: Number of pixels
        
        Returns:
            CSSUnitValue with "px" unit
        
        Example:
            width = CSS.px(100)  # 100px
        """
        ...
    
    @staticmethod
    def percent(value: float) -> CSSUnitValue:
        """
        Create a percentage value.
        
        Args:
            value: Percentage (0-100 for typical use)
        
        Returns:
            CSSUnitValue with "percent" unit
        
        Example:
            width = CSS.percent(50)  # 50%
        """
        ...
    
    @staticmethod
    def em(value: float) -> CSSUnitValue:
        """
        Create an em value (relative to font-size).
        
        Args:
            value: Number of ems
        
        Returns:
            CSSUnitValue with "em" unit
        
        Example:
            padding = CSS.em(1.5)  # 1.5em
        """
        ...
    
    @staticmethod
    def rem(value: float) -> CSSUnitValue:
        """
        Create a rem value (relative to root font-size).
        
        Args:
            value: Number of rems
        
        Returns:
            CSSUnitValue with "rem" unit
        
        Example:
            margin = CSS.rem(2)  # 2rem
        """
        ...
    
    @staticmethod
    def vw(value: float) -> CSSUnitValue:
        """
        Create a viewport width value.
        
        Args:
            value: Percentage of viewport width
        
        Returns:
            CSSUnitValue with "vw" unit
        
        Example:
            width = CSS.vw(100)  # 100vw (full viewport width)
        """
        ...
    
    @staticmethod
    def vh(value: float) -> CSSUnitValue:
        """
        Create a viewport height value.
        
        Args:
            value: Percentage of viewport height
        
        Returns:
            CSSUnitValue with "vh" unit
        
        Example:
            height = CSS.vh(100)  # 100vh (full viewport height)
        """
        ...
    
    @staticmethod
    def vmin(value: float) -> CSSUnitValue:
        """
        Create a vmin value (smaller of vw/vh).
        
        Args:
            value: Percentage of smaller viewport dimension
        
        Returns:
            CSSUnitValue with "vmin" unit
        """
        ...
    
    @staticmethod
    def vmax(value: float) -> CSSUnitValue:
        """
        Create a vmax value (larger of vw/vh).
        
        Args:
            value: Percentage of larger viewport dimension
        
        Returns:
            CSSUnitValue with "vmax" unit
        """
        ...
    
    # =========================================================================
    # Dynamic Viewport Units (CSS Level 4)
    # These account for dynamic browser UI like mobile address bars
    # =========================================================================
    
    @staticmethod
    def svw(value: float) -> CSSUnitValue:
        """
        Create a small viewport width value.
        
        WHO: Developers building mobile-responsive layouts
        WHAT: Viewport width when browser UI is fully visible (smallest)
        WHEN: Use for layouts that must fit when mobile keyboard/toolbar shown
        WHERE: Client-side code (transpiled to JavaScript)
        WHY: Prevents content being hidden by mobile browser UI
        HOW: Zero-runtime passthrough
        
        Args:
            value: Percentage of small viewport width
        
        Returns:
            CSSUnitValue with "svw" unit
        
        Example:
            width = CSS.svw(100)  # Full width even with mobile UI
        """
        ...
    
    @staticmethod
    def svh(value: float) -> CSSUnitValue:
        """
        Create a small viewport height value.
        
        The "small viewport" is the viewport size when browser UI
        (address bar, toolbar) is fully expanded.
        
        Args:
            value: Percentage of small viewport height
        
        Returns:
            CSSUnitValue with "svh" unit
        
        Example:
            height = CSS.svh(100)  # Full height with mobile UI visible
        """
        ...
    
    @staticmethod
    def lvw(value: float) -> CSSUnitValue:
        """
        Create a large viewport width value.
        
        Args:
            value: Percentage of large viewport width
        
        Returns:
            CSSUnitValue with "lvw" unit
        """
        ...
    
    @staticmethod
    def lvh(value: float) -> CSSUnitValue:
        """
        Create a large viewport height value.
        
        The "large viewport" is the viewport size when browser UI
        is minimized/hidden (user scrolled down on mobile).
        
        Args:
            value: Percentage of large viewport height
        
        Returns:
            CSSUnitValue with "lvh" unit
        
        Example:
            height = CSS.lvh(100)  # Full height with mobile UI hidden
        """
        ...
    
    @staticmethod
    def dvw(value: float) -> CSSUnitValue:
        """
        Create a dynamic viewport width value.
        
        Args:
            value: Percentage of dynamic viewport width
        
        Returns:
            CSSUnitValue with "dvw" unit
        """
        ...
    
    @staticmethod
    def dvh(value: float) -> CSSUnitValue:
        """
        Create a dynamic viewport height value.
        
        The "dynamic viewport" automatically adjusts as browser UI
        appears/disappears. This is the most flexible option.
        
        Args:
            value: Percentage of dynamic viewport height
        
        Returns:
            CSSUnitValue with "dvh" unit
        
        Example:
            # Hero section that adapts to mobile browser UI
            height = CSS.dvh(100)
        """
        ...
    
    # =========================================================================
    # Container Query Units (CSS Container Queries)
    # Relative to the nearest query container, not the viewport
    # =========================================================================
    
    @staticmethod
    def cqw(value: float) -> CSSUnitValue:
        """
        Create a container query width value.
        
        WHO: Developers building component-based responsive layouts
        WHAT: Percentage of the query container's width
        WHEN: Use for truly responsive components that adapt to their container
        WHERE: Client-side code (transpiled to JavaScript)
        WHY: Components respond to their container, not the viewport
        HOW: Zero-runtime passthrough
        
        Args:
            value: Percentage of container width
        
        Returns:
            CSSUnitValue with "cqw" unit
        
        Example:
            # Card width relative to its container
            width = CSS.cqw(50)  # 50% of container width
        """
        ...
    
    @staticmethod
    def cqh(value: float) -> CSSUnitValue:
        """
        Create a container query height value.
        
        Args:
            value: Percentage of container height
        
        Returns:
            CSSUnitValue with "cqh" unit
        """
        ...
    
    @staticmethod
    def cqi(value: float) -> CSSUnitValue:
        """
        Create a container query inline-size value.
        
        Inline-size is width in horizontal writing modes,
        height in vertical writing modes.
        
        Args:
            value: Percentage of container inline size
        
        Returns:
            CSSUnitValue with "cqi" unit
        """
        ...
    
    @staticmethod
    def cqb(value: float) -> CSSUnitValue:
        """
        Create a container query block-size value.
        
        Block-size is height in horizontal writing modes,
        width in vertical writing modes.
        
        Args:
            value: Percentage of container block size
        
        Returns:
            CSSUnitValue with "cqb" unit
        """
        ...
    
    @staticmethod
    def cqmin(value: float) -> CSSUnitValue:
        """
        Create a container query min value.
        
        The smaller of cqi (inline) or cqb (block) size.
        
        Args:
            value: Percentage of smaller container dimension
        
        Returns:
            CSSUnitValue with "cqmin" unit
        """
        ...
    
    @staticmethod
    def cqmax(value: float) -> CSSUnitValue:
        """
        Create a container query max value.
        
        The larger of cqi (inline) or cqb (block) size.
        
        Args:
            value: Percentage of larger container dimension
        
        Returns:
            CSSUnitValue with "cqmax" unit
        """
        ...
    
    # =========================================================================
    # Advanced Typography Units
    # =========================================================================
    
    @staticmethod
    def cap(value: float) -> CSSUnitValue:
        """
        Create a cap-height value.
        
        The cap-height is the height of capital letters in the font.
        
        Args:
            value: Number of cap-heights
        
        Returns:
            CSSUnitValue with "cap" unit
        
        Example:
            # Icon sized to match capital letter height
            size = CSS.cap(1)
        """
        ...
    
    @staticmethod
    def ic(value: float) -> CSSUnitValue:
        """
        Create an ic (ideographic character) value.
        
        The width of the CJK water ideograph (水). Useful for
        East Asian typography where characters have uniform width.
        
        Args:
            value: Number of ideographic character widths
        
        Returns:
            CSSUnitValue with "ic" unit
        """
        ...
    
    @staticmethod
    def lh(value: float) -> CSSUnitValue:
        """
        Create a line-height value.
        
        Relative to the element's computed line-height.
        
        Args:
            value: Number of line-heights
        
        Returns:
            CSSUnitValue with "lh" unit
        
        Example:
            # Margin equal to one line of text
            margin = CSS.lh(1)
        """
        ...
    
    @staticmethod
    def rlh(value: float) -> CSSUnitValue:
        """
        Create a root line-height value.
        
        Relative to the root element's (html) computed line-height.
        Like rem but for line-height instead of font-size.
        
        Args:
            value: Number of root line-heights
        
        Returns:
            CSSUnitValue with "rlh" unit
        """
        ...
    
    @staticmethod
    def ch(value: float) -> CSSUnitValue:
        """
        Create a ch value (width of "0" character).
        
        Args:
            value: Number of character widths
        
        Returns:
            CSSUnitValue with "ch" unit
        """
        ...
    
    @staticmethod
    def ex(value: float) -> CSSUnitValue:
        """
        Create an ex value (x-height of font).
        
        Args:
            value: Number of x-heights
        
        Returns:
            CSSUnitValue with "ex" unit
        """
        ...
    
    @staticmethod
    def cm(value: float) -> CSSUnitValue:
        """Create a centimeter value."""
        ...
    
    @staticmethod
    def mm(value: float) -> CSSUnitValue:
        """Create a millimeter value."""
        ...
    
    @staticmethod
    def Q(value: float) -> CSSUnitValue:
        """Create a quarter-millimeter value."""
        ...
    
    @staticmethod
    def in_(value: float) -> CSSUnitValue:
        """
        Create an inch value.
        
        Note: Named in_() to avoid Python keyword conflict.
        Transpiles to CSS.in()
        """
        ...
    
    @staticmethod
    def pt(value: float) -> CSSUnitValue:
        """Create a point value (1/72 inch)."""
        ...
    
    @staticmethod
    def pc(value: float) -> CSSUnitValue:
        """Create a pica value (12 points)."""
        ...
    
    # =========================================================================
    # Angle Units
    # =========================================================================
    
    @staticmethod
    def deg(value: float) -> CSSUnitValue:
        """
        Create a degree value.
        
        Args:
            value: Degrees (0-360 for full rotation)
        
        Returns:
            CSSUnitValue with "deg" unit
        
        Example:
            rotation = CSS.deg(45)  # 45deg
        """
        ...
    
    @staticmethod
    def rad(value: float) -> CSSUnitValue:
        """
        Create a radian value.
        
        Args:
            value: Radians (2π for full rotation)
        
        Returns:
            CSSUnitValue with "rad" unit
        
        Example:
            rotation = CSS.rad(3.14159)  # ~180deg
        """
        ...
    
    @staticmethod
    def grad(value: float) -> CSSUnitValue:
        """
        Create a gradian value.
        
        Args:
            value: Gradians (400 for full rotation)
        
        Returns:
            CSSUnitValue with "grad" unit
        """
        ...
    
    @staticmethod
    def turn(value: float) -> CSSUnitValue:
        """
        Create a turn value.
        
        Args:
            value: Number of turns (1 = 360deg)
        
        Returns:
            CSSUnitValue with "turn" unit
        
        Example:
            rotation = CSS.turn(0.5)  # 180deg
        """
        ...
    
    # =========================================================================
    # Time Units
    # =========================================================================
    
    @staticmethod
    def ms(value: float) -> CSSUnitValue:
        """
        Create a millisecond value.
        
        Args:
            value: Milliseconds
        
        Returns:
            CSSUnitValue with "ms" unit
        
        Example:
            duration = CSS.ms(300)  # 300ms
        """
        ...
    
    @staticmethod
    def s(value: float) -> CSSUnitValue:
        """
        Create a second value.
        
        Args:
            value: Seconds
        
        Returns:
            CSSUnitValue with "s" unit
        
        Example:
            duration = CSS.s(0.3)  # 0.3s
        """
        ...
    
    # =========================================================================
    # Frequency Units
    # =========================================================================
    
    @staticmethod
    def Hz(value: float) -> CSSUnitValue:
        """Create a Hertz value."""
        ...
    
    @staticmethod
    def kHz(value: float) -> CSSUnitValue:
        """Create a kilohertz value."""
        ...
    
    # =========================================================================
    # Resolution Units
    # =========================================================================
    
    @staticmethod
    def dpi(value: float) -> CSSUnitValue:
        """Create a dots-per-inch value."""
        ...
    
    @staticmethod
    def dpcm(value: float) -> CSSUnitValue:
        """Create a dots-per-centimeter value."""
        ...
    
    @staticmethod
    def dppx(value: float) -> CSSUnitValue:
        """Create a dots-per-pixel value."""
        ...
    
    # =========================================================================
    # Flex Units
    # =========================================================================
    
    @staticmethod
    def fr(value: float) -> CSSUnitValue:
        """
        Create a flex fraction value (for CSS Grid).
        
        Args:
            value: Number of fractions
        
        Returns:
            CSSUnitValue with "fr" unit
        
        Example:
            col_width = CSS.fr(1)  # 1fr
        """
        ...
    
    # =========================================================================
    # Unitless Values
    # =========================================================================
    
    @staticmethod
    def number(value: float) -> CSSUnitValue:
        """
        Create a unitless number.
        
        Args:
            value: The number
        
        Returns:
            CSSUnitValue with "number" unit
        
        Example:
            opacity_val = CSS.number(0.5)
            line_height = CSS.number(1.5)
        """
        ...
    
    # =========================================================================
    # Keywords
    # =========================================================================
    
    @staticmethod
    def keyword(value: str) -> CSSKeywordValue:
        """
        Create a CSS keyword value.
        
        Args:
            value: The keyword string
        
        Returns:
            CSSKeywordValue
        
        Example:
            auto = CSS.keyword("auto")
            inherit = CSS.keyword("inherit")
            flex = CSS.keyword("flex")
        """
        ...
    
    # =========================================================================
    # Math Functions
    # =========================================================================
    
    @staticmethod
    def calc(expression: str) -> CSSMathValue:
        """
        Create a calc() expression.
        
        Note: The expression is passed as a string and parsed by the browser.
        
        Args:
            expression: The calc expression (without "calc()")
        
        Returns:
            CSSMathValue representing the calculation
        
        Example:
            width = CSS.calc("100% - 20px")
            height = CSS.calc("50vh + 2rem")
        """
        ...
    
    @staticmethod
    def min(*values: CSSNumericValue) -> CSSMathMin:
        """
        Create a min() expression.
        
        Args:
            values: Values to find minimum of
        
        Returns:
            CSSMathMin
        
        Example:
            width = CSS.min(CSS.px(300), CSS.percent(100))
        """
        ...
    
    @staticmethod
    def max(*values: CSSNumericValue) -> CSSMathMax:
        """
        Create a max() expression.
        
        Args:
            values: Values to find maximum of
        
        Returns:
            CSSMathMax
        
        Example:
            width = CSS.max(CSS.px(100), CSS.percent(50))
        """
        ...
    
    @staticmethod
    def clamp(
        min_val: CSSNumericValue,
        val: CSSNumericValue,
        max_val: CSSNumericValue
    ) -> CSSMathClamp:
        """
        Create a clamp() expression.
        
        Args:
            min_val: Minimum allowed value
            val: Preferred value
            max_val: Maximum allowed value
        
        Returns:
            CSSMathClamp
        
        Example:
            font_size = CSS.clamp(CSS.px(12), CSS.vw(2), CSS.px(24))
        """
        ...
    
    # =========================================================================
    # Transform Factory Methods
    # =========================================================================
    
    @staticmethod
    def translate(
        x: CSSNumericValue,
        y: Optional[CSSNumericValue] = None,
        z: Optional[CSSNumericValue] = None
    ) -> CSSTranslate:
        """
        Create a translate() transform.
        
        Args:
            x: X translation
            y: Y translation (default: 0)
            z: Z translation (for 3D, default: 0)
        
        Returns:
            CSSTranslate component
        
        Example:
            move = CSS.translate(CSS.px(100), CSS.px(50))
        """
        ...
    
    @staticmethod
    def translateX(x: CSSNumericValue) -> CSSTranslate:
        """Create a translateX() transform."""
        ...
    
    @staticmethod
    def translateY(y: CSSNumericValue) -> CSSTranslate:
        """Create a translateY() transform."""
        ...
    
    @staticmethod
    def translateZ(z: CSSNumericValue) -> CSSTranslate:
        """Create a translateZ() transform."""
        ...
    
    @staticmethod
    def translate3d(
        x: CSSNumericValue,
        y: CSSNumericValue,
        z: CSSNumericValue
    ) -> CSSTranslate:
        """Create a translate3d() transform."""
        ...
    
    @staticmethod
    def rotate(angle: CSSNumericValue) -> CSSRotate:
        """
        Create a rotate() transform.
        
        Args:
            angle: Rotation angle
        
        Returns:
            CSSRotate component
        
        Example:
            spin = CSS.rotate(CSS.deg(45))
        """
        ...
    
    @staticmethod
    def rotateX(angle: CSSNumericValue) -> CSSRotate:
        """Create a rotateX() transform."""
        ...
    
    @staticmethod
    def rotateY(angle: CSSNumericValue) -> CSSRotate:
        """Create a rotateY() transform."""
        ...
    
    @staticmethod
    def rotateZ(angle: CSSNumericValue) -> CSSRotate:
        """Create a rotateZ() transform."""
        ...
    
    @staticmethod
    def rotate3d(
        x: float,
        y: float,
        z: float,
        angle: CSSNumericValue
    ) -> CSSRotate:
        """Create a rotate3d() transform."""
        ...
    
    @staticmethod
    def scale(
        x: float,
        y: Optional[float] = None,
        z: Optional[float] = None
    ) -> CSSScale:
        """
        Create a scale() transform.
        
        Args:
            x: X scale factor
            y: Y scale factor (default: same as x)
            z: Z scale factor (for 3D, default: 1)
        
        Returns:
            CSSScale component
        
        Example:
            grow = CSS.scale(2)  # 2x in both directions
            stretch = CSS.scale(2, 1)  # 2x width, normal height
        """
        ...
    
    @staticmethod
    def scaleX(x: float) -> CSSScale:
        """Create a scaleX() transform."""
        ...
    
    @staticmethod
    def scaleY(y: float) -> CSSScale:
        """Create a scaleY() transform."""
        ...
    
    @staticmethod
    def scaleZ(z: float) -> CSSScale:
        """Create a scaleZ() transform."""
        ...
    
    @staticmethod
    def scale3d(x: float, y: float, z: float) -> CSSScale:
        """Create a scale3d() transform."""
        ...
    
    @staticmethod
    def skew(ax: CSSNumericValue, ay: Optional[CSSNumericValue] = None) -> CSSSkew:
        """
        Create a skew() transform.
        
        Args:
            ax: X-axis skew angle
            ay: Y-axis skew angle (default: 0)
        
        Returns:
            CSSSkew component
        """
        ...
    
    @staticmethod
    def skewX(ax: CSSNumericValue) -> CSSSkewX:
        """Create a skewX() transform."""
        ...
    
    @staticmethod
    def skewY(ay: CSSNumericValue) -> CSSSkewY:
        """Create a skewY() transform."""
        ...
    
    @staticmethod
    def perspective(length: CSSNumericValue) -> CSSPerspective:
        """
        Create a perspective() transform.
        
        Args:
            length: Perspective distance
        
        Returns:
            CSSPerspective component
        """
        ...
    
    @staticmethod
    def matrix(
        a: float, b: float, c: float, d: float, e: float, f: float
    ) -> CSSMatrixComponent:
        """
        Create a 2D matrix() transform.
        
        Args:
            a, b, c, d, e, f: 2D matrix components
        
        Returns:
            CSSMatrixComponent
        """
        ...
    
    @staticmethod
    def matrix3d(
        m11: float, m12: float, m13: float, m14: float,
        m21: float, m22: float, m23: float, m24: float,
        m31: float, m32: float, m33: float, m34: float,
        m41: float, m42: float, m43: float, m44: float,
    ) -> CSSMatrixComponent:
        """
        Create a 3D matrix3d() transform.
        
        Args:
            m11-m44: 4x4 matrix components
        
        Returns:
            CSSMatrixComponent
        """
        ...
    
    # =========================================================================
    # Parsing
    # =========================================================================
    
    @staticmethod
    def parse(property: str, value: str) -> CSSStyleValue:
        """
        Parse a CSS value string into a typed value.
        
        Args:
            property: CSS property name
            value: CSS value string
        
        Returns:
            Appropriate CSSStyleValue subtype
        
        Example:
            width = CSS.parse("width", "100px")  # CSSUnitValue
        """
        ...
    
    @staticmethod
    def parseAll(property: str, value: str) -> List[CSSStyleValue]:
        """
        Parse a CSS value that may expand to multiple values.
        
        Args:
            property: CSS property name
            value: CSS value string
        
        Returns:
            List of CSSStyleValue objects
        """
        ...
    
    # =========================================================================
    # Registration (CSS Houdini)
    # =========================================================================
    
    @staticmethod
    def registerProperty(definition: dict) -> None:
        """
        Register a custom CSS property.
        
        Args:
            definition: Property definition with name, syntax, inherits, initialValue
        
        Example:
            CSS.registerProperty({
                "name": "--my-color",
                "syntax": "<color>",
                "inherits": False,
                "initialValue": "black",
            })
        """
        ...
    
    # =========================================================================
    # Feature Detection
    # =========================================================================
    
    @staticmethod
    def supports(property_or_condition: str, value: Optional[str] = None) -> bool:
        """
        Check if the browser supports a CSS feature.
        
        WHO: Developers implementing progressive enhancement
        WHAT: Feature detection for CSS properties/values
        WHEN: Before using potentially unsupported CSS features
        WHERE: Client-side code (transpiled to JavaScript)
        WHY: Graceful degradation and progressive enhancement
        HOW: Zero-runtime passthrough to CSS.supports()
        
        Args:
            property_or_condition: CSS property name or full condition string
            value: Optional CSS value (if first arg is property name)
        
        Returns:
            True if the feature is supported
        
        Examples:
            # Check property + value
            if CSS.supports("display", "grid"):
                use_grid_layout()
            
            # Check condition string
            if CSS.supports("(display: flex) and (gap: 10px)"):
                use_flex_gap()
        """
        ...
    
    @staticmethod
    def escape(ident: str) -> str:
        """
        Escape a string for use in CSS selectors.
        
        WHO: Developers using dynamic IDs/classes in selectors
        WHAT: Escapes special characters in CSS identifiers
        WHEN: When using user-provided or dynamic values in selectors
        WHERE: Client-side code (transpiled to JavaScript)
        WHY: Prevents selector injection and syntax errors
        HOW: Zero-runtime passthrough to CSS.escape()
        
        Args:
            ident: The identifier string to escape
        
        Returns:
            Escaped string safe for use in selectors
        
        Example:
            # Escape user-provided ID
            safe_id = CSS.escape("my#special.class")
            el = document.querySelector("#" + safe_id)
            
            # In f-string
            el = document.querySelector(f"[data-id='{CSS.escape(user_id)}']")
        """
        ...
    
    # =========================================================================
    # Image Values
    # =========================================================================
    
    @staticmethod
    def url(url: str) -> CSSURLImageValue:
        """
        Create a url() image value.
        
        Args:
            url: The URL path to the image
        
        Returns:
            CSSURLImageValue
        
        Example:
            bg = CSS.url("/images/background.png")
            el.attributeStyleMap.set("background-image", bg)
        """
        ...
    
    @staticmethod
    def linearGradient(direction: str, stops: List[str]) -> CSSLinearGradient:
        """
        Create a linear-gradient() value.
        
        Args:
            direction: Gradient direction (e.g., "to right", "45deg")
            stops: Color stops (e.g., ["red", "blue"])
        
        Returns:
            CSSLinearGradient
        
        Example:
            gradient = CSS.linearGradient("to right", ["#ff0000", "#0000ff"])
        """
        ...
    
    @staticmethod
    def radialGradient(shape: str, stops: List[str]) -> CSSRadialGradient:
        """
        Create a radial-gradient() value.
        
        Args:
            shape: Gradient shape (e.g., "circle", "ellipse at center")
            stops: Color stops
        
        Returns:
            CSSRadialGradient
        
        Example:
            gradient = CSS.radialGradient("circle", ["yellow", "transparent"])
        """
        ...
    
    @staticmethod
    def conicGradient(angle: str, stops: List[str]) -> CSSConicGradient:
        """
        Create a conic-gradient() value.
        
        Args:
            angle: Starting angle (e.g., "from 0deg")
            stops: Color stops
        
        Returns:
            CSSConicGradient
        
        Example:
            gradient = CSS.conicGradient("from 0deg", ["red", "blue", "red"])
        """
        ...


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Factory namespace
    "CSS",
    
    # Core value types
    "CSSStyleValue",
    "CSSNumericValue",
    "CSSUnitValue",
    "CSSKeywordValue",
    "CSSUnparsedValue",
    "CSSVariableReferenceValue",
    
    # Math values
    "CSSMathValue",
    "CSSMathSum",
    "CSSMathProduct",
    "CSSMathNegate",
    "CSSMathInvert",
    "CSSMathMin",
    "CSSMathMax",
    "CSSMathClamp",
    "CSSNumericType",
    
    # Transform values
    "CSSTransformValue",
    "CSSTransformComponent",
    "CSSTranslate",
    "CSSRotate",
    "CSSScale",
    "CSSSkew",
    "CSSSkewX",
    "CSSSkewY",
    "CSSPerspective",
    "CSSMatrixComponent",
    "DOMMatrix",
    
    # Image values
    "CSSImageValue",
    "CSSURLImageValue",
    "CSSLinearGradient",
    "CSSRadialGradient",
    "CSSConicGradient",
    
    # Style maps
    "StylePropertyMapReadOnly",
    "StylePropertyMap",
]
