/**
 * PyNext Runtime - datetime Module
 * 
 * WHAT THIS FILE DOES:
 * Provides Python datetime module functionality in JavaScript.
 * Implements date, time, datetime, timedelta, and timezone classes.
 * 
 * WHY THIS EXISTS:
 * Python developers expect datetime functionality to work the same way
 * in client-side code. This module provides Python-compatible datetime APIs.
 * 
 * HOW IT WORKS:
 * - Uses JavaScript Date internally but provides Python API
 * - Handles timezone conversions
 * - Supports strftime/strptime formatting
 * - Optimized for common use cases
 * 
 * WHO USES THIS:
 * - Transpiled Python code using datetime
 * - Client-side code needing datetime functionality
 * 
 * WHEN TO USE:
 * - Date/time operations: datetime, date, time
 * - Duration calculations: timedelta
 * - Timezone handling: timezone
 * - Formatting: strftime/strptime
 * 
 * EXAMPLES:
 *     // In Python:
 *     from pynext.client.datetime import datetime, timedelta
 *     now = datetime.now()
 *     tomorrow = now + timedelta(days=1)
 *     
 *     // Transpiles to JavaScript using this module
 */

/**
 * Timezone class - represents a timezone offset.
 */
export class timezone {
    constructor(offset = null, name = null) {
        if (offset === null) {
            offset = new timedelta(0);
        }
        if (!(offset instanceof timedelta)) {
            throw new TypeError('offset must be a timedelta');
        }
        if (offset.microseconds !== 0 || offset.seconds % 3600 !== 0) {
            throw new ValueError('offset must be a whole number of minutes');
        }
        this._offset = offset;
        this._name = name;
    }
    
    get utcoffset() {
        return this._offset;
    }
    
    get tzname() {
        return this._name || `UTC${this._offset >= timedelta(0) ? '+' : ''}${this._offset}`;
    }
    
    dst(dt) {
        // Python datetime.timezone doesn't observe DST
        return timedelta(0);
    }
    
    toString() {
        return this.tzname;
    }
}

// UTC timezone
export const UTC = new timezone(timedelta(0), 'UTC');

/**
 * timedelta class - represents a duration, the difference between two dates or times.
 */
export class timedelta {
    constructor(days = 0, seconds = 0, microseconds = 0, milliseconds = 0, minutes = 0, hours = 0, weeks = 0) {
        // Convert everything to microseconds for internal storage
        this.days = days + (weeks * 7);
        this.seconds = seconds + (minutes * 60) + (hours * 3600);
        this.microseconds = microseconds + (milliseconds * 1000);
        
        // Normalize
        this._normalize();
    }
    
    _normalize() {
        // Normalize seconds and microseconds
        let total_seconds = this.seconds;
        let total_microseconds = this.microseconds;
        
        // Convert microseconds to seconds
        total_seconds += Math.floor(total_microseconds / 1000000);
        total_microseconds = total_microseconds % 1000000;
        if (total_microseconds < 0) {
            total_seconds -= 1;
            total_microseconds += 1000000;
        }
        
        // Convert seconds to days
        this.days += Math.floor(total_seconds / 86400);
        this.seconds = total_seconds % 86400;
        if (this.seconds < 0) {
            this.days -= 1;
            this.seconds += 86400;
        }
        
        this.microseconds = total_microseconds;
    }
    
    total_seconds() {
        return (this.days * 86400) + this.seconds + (this.microseconds / 1000000);
    }
    
    _add(other) {
        if (other instanceof timedelta) {
            return new timedelta(
                this.days + other.days,
                this.seconds + other.seconds,
                this.microseconds + other.microseconds
            );
        }
        throw new TypeError('Can only add timedelta to timedelta');
    }
    
    _sub(other) {
        if (other instanceof timedelta) {
            return new timedelta(
                this.days - other.days,
                this.seconds - other.seconds,
                this.microseconds - other.microseconds
            );
        }
        throw new TypeError('Can only subtract timedelta from timedelta');
    }
    
    _mul(other) {
        if (typeof other === 'number') {
            return new timedelta(
                this.days * other,
                this.seconds * other,
                this.microseconds * other
            );
        }
        throw new TypeError('Can only multiply timedelta by number');
    }
    
    _truediv(other) {
        if (other instanceof timedelta) {
            return this.total_seconds() / other.total_seconds();
        }
        if (typeof other === 'number') {
            return new timedelta(
                this.days / other,
                this.seconds / other,
                this.microseconds / other
            );
        }
        throw new TypeError('Can only divide timedelta by timedelta or number');
    }
    
    _floordiv(other) {
        if (other instanceof timedelta) {
            return Math.floor(this.total_seconds() / other.total_seconds());
        }
        if (typeof other === 'number') {
            const result = this._truediv(other);
            return new timedelta(
                Math.floor(result.days),
                Math.floor(result.seconds),
                Math.floor(result.microseconds)
            );
        }
        throw new TypeError('Can only floor-divide timedelta by timedelta or number');
    }
    
    _mod(other) {
        if (other instanceof timedelta) {
            const quotient = this._floordiv(other);
            return this._sub(other._mul(quotient));
        }
        throw new TypeError('Can only mod timedelta by timedelta');
    }
    
    _neg() {
        return new timedelta(-this.days, -this.seconds, -this.microseconds);
    }
    
    _pos() {
        return new timedelta(this.days, this.seconds, this.microseconds);
    }
    
    _abs() {
        if (this.days < 0 || (this.days === 0 && this.seconds < 0)) {
            return this._neg();
        }
        return this._pos();
    }
    
    _eq(other) {
        if (!(other instanceof timedelta)) {
            return false;
        }
        return this.days === other.days && 
               this.seconds === other.seconds && 
               this.microseconds === other.microseconds;
    }
    
    _lt(other) {
        if (!(other instanceof timedelta)) {
            return NotImplemented;
        }
        if (this.days !== other.days) {
            return this.days < other.days;
        }
        if (this.seconds !== other.seconds) {
            return this.seconds < other.seconds;
        }
        return this.microseconds < other.microseconds;
    }
    
    _le(other) {
        return this._eq(other) || this._lt(other);
    }
    
    _gt(other) {
        if (!(other instanceof timedelta)) {
            return NotImplemented;
        }
        return !this._le(other);
    }
    
    _ge(other) {
        return this._eq(other) || this._gt(other);
    }
    
    toString() {
        let parts = [];
        if (this.days !== 0) {
            parts.push(`${this.days} day${this.days !== 1 ? 's' : ''}`);
        }
        if (this.seconds !== 0 || this.microseconds !== 0 || parts.length === 0) {
            let secs = this.seconds;
            if (this.microseconds !== 0) {
                secs += this.microseconds / 1000000;
            }
            parts.push(`${secs} second${secs !== 1 ? 's' : ''}`);
        }
        return parts.join(', ');
    }
}

// Constants
export const MINYEAR = 1;
export const MAXYEAR = 9999;

// Helper to create timedelta from days
function _days_to_timedelta(days) {
    return new timedelta(days, 0, 0);
}

/**
 * date class - represents a date (year, month, day).
 */
export class date {
    constructor(year, month, day) {
        if (year < MINYEAR || year > MAXYEAR) {
            throw new ValueError(`year must be in ${MINYEAR}..${MAXYEAR}`);
        }
        if (month < 1 || month > 12) {
            throw new ValueError('month must be in 1..12');
        }
        
        // Create JS Date to validate day
        const jsDate = new Date(year, month - 1, day);
        if (jsDate.getFullYear() !== year || 
            jsDate.getMonth() !== month - 1 || 
            jsDate.getDate() !== day) {
            throw new ValueError('day is out of range for month');
        }
        
        this.year = year;
        this.month = month;
        this.day = day;
    }
    
    static today() {
        const now = new Date();
        return new date(now.getFullYear(), now.getMonth() + 1, now.getDate());
    }
    
    static fromtimestamp(timestamp) {
        const d = new Date(timestamp * 1000);
        return new date(d.getFullYear(), d.getMonth() + 1, d.getDate());
    }
    
    static fromordinal(ordinal) {
        // Convert ordinal day number to date
        // This is a simplified version
        const epoch = new Date(1970, 0, 1);
        const target = new Date(epoch.getTime() + (ordinal - 719163) * 86400000);
        return new date(target.getFullYear(), target.getMonth() + 1, target.getDate());
    }
    
    toordinal() {
        const epoch = new Date(1970, 0, 1);
        const d = new Date(this.year, this.month - 1, this.day);
        return Math.floor((d - epoch) / 86400000) + 719163;
    }
    
    weekday() {
        const d = new Date(this.year, this.month - 1, this.day);
        const day = d.getDay();
        return (day + 6) % 7; // Monday = 0, Sunday = 6
    }
    
    isoweekday() {
        const d = new Date(this.year, this.month - 1, this.day);
        return d.getDay() || 7; // Monday = 1, Sunday = 7
    }
    
    isoformat() {
        return `${this.year.toString().padStart(4, '0')}-${this.month.toString().padStart(2, '0')}-${this.day.toString().padStart(2, '0')}`;
    }
    
    strftime(format) {
        // Simplified strftime implementation
        return format
            .replace('%Y', this.year.toString().padStart(4, '0'))
            .replace('%m', this.month.toString().padStart(2, '0'))
            .replace('%d', this.day.toString().padStart(2, '0'))
            .replace('%B', ['January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December'][this.month - 1])
            .replace('%b', ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][this.month - 1])
            .replace('%A', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][this.weekday()])
            .replace('%a', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][this.weekday()]);
    }
    
    _sub(other) {
        if (other instanceof date) {
            const thisOrdinal = this.toordinal();
            const otherOrdinal = other.toordinal();
            return _days_to_timedelta(thisOrdinal - otherOrdinal);
        }
        if (other instanceof timedelta) {
            const ordinal = this.toordinal() - other.days;
            return date.fromordinal(ordinal);
        }
        throw new TypeError('Can only subtract date or timedelta from date');
    }
    
    _eq(other) {
        return other instanceof date &&
               this.year === other.year &&
               this.month === other.month &&
               this.day === other.day;
    }
    
    _lt(other) {
        if (!(other instanceof date)) {
            return NotImplemented;
        }
        if (this.year !== other.year) {
            return this.year < other.year;
        }
        if (this.month !== other.month) {
            return this.month < other.month;
        }
        return this.day < other.day;
    }
    
    toString() {
        return this.isoformat();
    }
}

/**
 * time class - represents a time (hour, minute, second, microsecond).
 */
export class time {
    constructor(hour = 0, minute = 0, second = 0, microsecond = 0, tzinfo = null, fold = 0) {
        if (hour < 0 || hour > 23) {
            throw new ValueError('hour must be in 0..23');
        }
        if (minute < 0 || minute > 59) {
            throw new ValueError('minute must be in 0..59');
        }
        if (second < 0 || second > 59) {
            throw new ValueError('second must be in 0..59');
        }
        if (microsecond < 0 || microsecond > 999999) {
            throw new ValueError('microsecond must be in 0..999999');
        }
        
        this.hour = hour;
        this.minute = minute;
        this.second = second;
        this.microsecond = microsecond;
        this.tzinfo = tzinfo;
        this.fold = fold;
    }
    
    isoformat() {
        let result = `${this.hour.toString().padStart(2, '0')}:${this.minute.toString().padStart(2, '0')}:${this.second.toString().padStart(2, '0')}`;
        if (this.microsecond !== 0) {
            result += `.${this.microsecond.toString().padStart(6, '0')}`;
        }
        if (this.tzinfo !== null) {
            result += this.tzinfo.tzname();
        }
        return result;
    }
    
    strftime(format) {
        // Simplified strftime for time
        return format
            .replace('%H', this.hour.toString().padStart(2, '0'))
            .replace('%M', this.minute.toString().padStart(2, '0'))
            .replace('%S', this.second.toString().padStart(2, '0'))
            .replace('%f', this.microsecond.toString().padStart(6, '0'));
    }
    
    _eq(other) {
        return other instanceof time &&
               this.hour === other.hour &&
               this.minute === other.minute &&
               this.second === other.second &&
               this.microsecond === other.microsecond &&
               this.tzinfo === other.tzinfo;
    }
    
    toString() {
        return this.isoformat();
    }
}

/**
 * datetime class - represents a date and time.
 */
export class datetime {
    constructor(year, month, day, hour = 0, minute = 0, second = 0, microsecond = 0, tzinfo = null, fold = 0) {
        this._date = new date(year, month, day);
        this._time = new time(hour, minute, second, microsecond, tzinfo, fold);
        
        this.year = year;
        this.month = month;
        this.day = day;
        this.hour = hour;
        this.minute = minute;
        this.second = second;
        this.microsecond = microsecond;
        this.tzinfo = tzinfo;
        this.fold = fold;
    }
    
    static now(tz = null) {
        const now = new Date();
        const dt = new datetime(
            now.getFullYear(),
            now.getMonth() + 1,
            now.getDate(),
            now.getHours(),
            now.getMinutes(),
            now.getSeconds(),
            now.getMilliseconds() * 1000,
            tz
        );
        return dt;
    }
    
    static utcnow() {
        return datetime.now(UTC);
    }
    
    static fromtimestamp(timestamp, tz = null) {
        const d = new Date(timestamp * 1000);
        return new datetime(
            d.getUTCFullYear(),
            d.getUTCMonth() + 1,
            d.getUTCDate(),
            d.getUTCHours(),
            d.getUTCMinutes(),
            d.getUTCSeconds(),
            d.getUTCMilliseconds() * 1000,
            tz || UTC
        );
    }
    
    static fromisoformat(date_string) {
        // Simplified ISO format parser: YYYY-MM-DD[THH:MM:SS[.ffffff]][+HH:MM]
        const match = date_string.match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?)?(?:([+-])(\d{2}):(\d{2}))?/);
        if (!match) {
            throw new ValueError('Invalid ISO format string');
        }
        
        const [, year, month, day, hour, minute, second, microsecond, tzsign, tzhour, tzminute] = match;
        
        let tz = null;
        if (tzsign) {
            const offset_hours = parseInt(tzhour);
            const offset_minutes = parseInt(tzminute);
            const total_minutes = (tzsign === '+' ? 1 : -1) * (offset_hours * 60 + offset_minutes);
            tz = new timezone(new timedelta(0, total_minutes * 60));
        }
        
        return new datetime(
            parseInt(year),
            parseInt(month),
            parseInt(day),
            hour ? parseInt(hour) : 0,
            minute ? parseInt(minute) : 0,
            second ? parseInt(second) : 0,
            microsecond ? parseInt(microsecond.padEnd(6, '0')) : 0,
            tz
        );
    }
    
    date() {
        return new date(this.year, this.month, this.day);
    }
    
    time() {
        return new time(this.hour, this.minute, this.second, this.microsecond, this.tzinfo);
    }
    
    timestamp() {
        // Convert to Unix timestamp
        const jsDate = new Date(
            Date.UTC(
                this.year,
                this.month - 1,
                this.day,
                this.hour,
                this.minute,
                this.second,
                Math.floor(this.microsecond / 1000)
            )
        );
        return jsDate.getTime() / 1000;
    }
    
    isoformat(sep = 'T', timespec = 'auto') {
        let result = `${this.year.toString().padStart(4, '0')}-${this.month.toString().padStart(2, '0')}-${this.day.toString().padStart(2, '0')}${sep}`;
        result += `${this.hour.toString().padStart(2, '0')}:${this.minute.toString().padStart(2, '0')}:${this.second.toString().padStart(2, '0')}`;
        
        if (timespec === 'microseconds' || (timespec === 'auto' && this.microsecond !== 0)) {
            result += `.${this.microsecond.toString().padStart(6, '0')}`;
        }
        
        if (this.tzinfo !== null) {
            result += this.tzinfo.tzname();
        }
        
        return result;
    }
    
    strftime(format) {
        // Combined date and time strftime
        return this.date().strftime(format)
            .replace('%H', this.hour.toString().padStart(2, '0'))
            .replace('%M', this.minute.toString().padStart(2, '0'))
            .replace('%S', this.second.toString().padStart(2, '0'))
            .replace('%f', this.microsecond.toString().padStart(6, '0'));
    }
    
    strptime(date_string, format) {
        // Simplified strptime - this is a complex function, simplified version
        throw new NotImplementedError('strptime not fully implemented');
    }
    
    replace(year = null, month = null, day = null, hour = null, minute = null, 
            second = null, microsecond = null, tzinfo = undefined, fold = undefined) {
        return new datetime(
            year !== null ? year : this.year,
            month !== null ? month : this.month,
            day !== null ? day : this.day,
            hour !== null ? hour : this.hour,
            minute !== null ? minute : this.minute,
            second !== null ? second : this.second,
            microsecond !== null ? microsecond : this.microsecond,
            tzinfo !== undefined ? tzinfo : this.tzinfo,
            fold !== undefined ? fold : this.fold
        );
    }
    
    _add(other) {
        if (other instanceof timedelta) {
            const jsDate = new Date(
                this.year,
                this.month - 1,
                this.day,
                this.hour,
                this.minute,
                this.second,
                Math.floor(this.microsecond / 1000)
            );
            jsDate.setTime(jsDate.getTime() + (other.total_seconds() * 1000));
            return new datetime(
                jsDate.getFullYear(),
                jsDate.getMonth() + 1,
                jsDate.getDate(),
                jsDate.getHours(),
                jsDate.getMinutes(),
                jsDate.getSeconds(),
                (jsDate.getMilliseconds() * 1000) + (other.microseconds % 1000),
                this.tzinfo
            );
        }
        throw new TypeError('Can only add timedelta to datetime');
    }
    
    _sub(other) {
        if (other instanceof timedelta) {
            return this._add(other._neg());
        }
        if (other instanceof datetime) {
            const thisTimestamp = this.timestamp();
            const otherTimestamp = other.timestamp();
            return new timedelta(0, thisTimestamp - otherTimestamp);
        }
        throw new TypeError('Can only subtract timedelta or datetime from datetime');
    }
    
    _eq(other) {
        return other instanceof datetime &&
               this.year === other.year &&
               this.month === other.month &&
               this.day === other.day &&
               this.hour === other.hour &&
               this.minute === other.minute &&
               this.second === other.second &&
               this.microsecond === other.microsecond &&
               this.tzinfo === other.tzinfo;
    }
    
    _lt(other) {
        if (!(other instanceof datetime)) {
            return NotImplemented;
        }
        const thisTimestamp = this.timestamp();
        const otherTimestamp = other.timestamp();
        return thisTimestamp < otherTimestamp;
    }
    
    toString() {
        return this.isoformat();
    }
}

// Helper error classes
class ValueError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValueError';
    }
}

class TypeError extends Error {
    constructor(message) {
        super(message);
        this.name = 'TypeError';
    }
}

class NotImplementedError extends Error {
    constructor(message) {
        super(message);
        this.name = 'NotImplementedError';
    }
}

const NotImplemented = Symbol('NotImplemented');

// Default exports
export default {
    date,
    time,
    datetime,
    timedelta,
    timezone,
    UTC,
    MINYEAR,
    MAXYEAR,
};

